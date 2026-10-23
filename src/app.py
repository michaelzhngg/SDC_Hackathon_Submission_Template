from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from ai_extractor import AIExtractionUnavailable, extract_supplier_message
from supplier_radar import build_supplier_radar
from workflow import OrderGuardService


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("ORDERGUARD_DB", str(BASE_DIR / "orderguard.db"))

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "vortex-orderguard-demo")
service = OrderGuardService(DB_PATH)


def _number(name: str) -> float:
    return float(request.form[name])


@app.get("/")
def dashboard():
    cases = service.list_cases()
    return render_template(
        "dashboard.html",
        cases=cases,
        outbox=service.get_outbox(),
        summary=service.get_dashboard_summary(),
        supplier_radar=build_supplier_radar(cases, service.get_supplier_insight),
        ai_enabled=bool(os.getenv("DEEPSEEK_API_KEY")),
    )


@app.post("/api/extract")
def extract_message():
    message = (request.get_json(silent=True) or {}).get("message", "").strip()
    if not message:
        return jsonify({"ok": False, "error": "Supplier message is required."}), 400
    try:
        data = extract_supplier_message(message)
    except AIExtractionUnavailable as exc:
        return jsonify({"ok": False, "error": str(exc), "fallback": "manual"}), 503
    except Exception:
        return jsonify(
            {
                "ok": False,
                "error": "AI extraction failed. Please confirm the structured fields manually.",
                "fallback": "manual",
            }
        ), 502
    return jsonify({"ok": True, "data": data, "requires_human_confirmation": True})


@app.route("/cases/new", methods=["GET", "POST"])
def new_case():
    if request.method == "POST":
        purchase_order = {
            "item": request.form["item"].strip(),
            "quantity": _number("po_quantity"),
            "unit": request.form["po_unit"].strip(),
            "unit_price": _number("po_price"),
        }
        received = {
            "item": request.form["item"].strip(),
            "quantity": _number("received_quantity"),
            "unit": request.form["received_unit"].strip(),
        }
        invoice = {
            "item": request.form["item"].strip(),
            "quantity": _number("invoice_quantity"),
            "unit": request.form["invoice_unit"].strip(),
            "unit_price": _number("invoice_price"),
        }
        case_id = service.create_case(
            supplier_message=request.form["supplier_message"].strip(),
            purchase_order=purchase_order,
            received=received,
            invoice=invoice,
            submitted_by="staff-demo",
            supplier_name=request.form.get("supplier_name", "Demo Supplier").strip(),
        )
        return redirect(url_for("case_detail", case_id=case_id))
    return render_template("new_case.html")


@app.post("/demo/scenario/<scenario>")
def demo_scenario(scenario: str):
    scenarios = {
        "discrepancy": {
            "supplier": "FreshFarm Foods",
            "message": "Delivered 8 kg chicken. Invoice 10 kg at RM13/kg.",
            "po": {"item": "Chicken", "quantity": 10, "unit": "kg", "unit_price": 12},
            "received": {"item": "Chicken", "quantity": 8, "unit": "kg"},
            "invoice": {"item": "Chicken", "quantity": 10, "unit": "kg", "unit_price": 13},
        },
        "repeat": {
            "supplier": "FreshFarm Foods",
            "message": "Second delivery: 8 kg chicken received. Invoice still 10 kg at RM13/kg.",
            "po": {"item": "Chicken", "quantity": 10, "unit": "kg", "unit_price": 12},
            "received": {"item": "Chicken", "quantity": 8, "unit": "kg"},
            "invoice": {"item": "Chicken", "quantity": 10, "unit": "kg", "unit_price": 13},
        },
        "match": {
            "supplier": "Golden Egg Trading",
            "message": "Delivered 30 trays eggs as ordered at RM8 per tray.",
            "po": {"item": "Eggs", "quantity": 30, "unit": "tray", "unit_price": 8},
            "received": {"item": "Eggs", "quantity": 30, "unit": "tray"},
            "invoice": {"item": "Eggs", "quantity": 30, "unit": "tray", "unit_price": 8},
        },
        "ambiguous": {
            "supplier": "RiceHub Supply",
            "message": "Delivered two bags rice. Invoice remains 10 kg at RM4/kg.",
            "po": {"item": "Rice", "quantity": 10, "unit": "kg", "unit_price": 4},
            "received": {"item": "Rice", "quantity": 2, "unit": "bags"},
            "invoice": {"item": "Rice", "quantity": 10, "unit": "kg", "unit_price": 4},
        },
    }
    data = scenarios.get(scenario)
    if data is None:
        flash("Unknown demo scenario.", "danger")
        return redirect(url_for("dashboard"))
    case_id = service.create_case(
        data["message"],
        data["po"],
        data["received"],
        data["invoice"],
        "demo-staff",
        supplier_name=data["supplier"],
    )
    return redirect(url_for("case_detail", case_id=case_id))


@app.get("/cases/<int:case_id>")
def case_detail(case_id: int):
    return render_template(
        "case_detail.html",
        case=service.get_case(case_id),
        activity=service.get_activity(case_id),
        supplier_insight=service.get_supplier_insight(case_id),
    )


@app.post("/cases/<int:case_id>/clarify")
def clarify_case(case_id: int):
    try:
        service.clarify_case(
            case_id,
            actor="owner-demo",
            received_quantity=_number("received_quantity"),
            received_unit=request.form["received_unit"].strip(),
        )
        flash("Human clarification recorded. The case was recalculated.", "success")
    except (ValueError, KeyError) as exc:
        flash(str(exc), "danger")
    return redirect(url_for("case_detail", case_id=case_id))


@app.post("/cases/<int:case_id>/approve")
def approve_case(case_id: int):
    try:
        service.approve_case(case_id, actor="owner-demo", role="owner")
        flash("Approved. The clarification was added to the simulated outbox.", "success")
    except (PermissionError, ValueError, KeyError) as exc:
        flash(str(exc), "danger")
    return redirect(url_for("case_detail", case_id=case_id))


@app.post("/cases/<int:case_id>/reject")
def reject_case(case_id: int):
    try:
        service.reject_case(
            case_id,
            actor="owner-demo",
            role="owner",
            reason=request.form.get("reason", "Owner rejected the proposed action"),
        )
        flash("Rejected. No supplier action was created.", "warning")
    except (PermissionError, ValueError, KeyError) as exc:
        flash(str(exc), "danger")
    return redirect(url_for("case_detail", case_id=case_id))


@app.post("/demo/reset")
def reset_demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    global service
    service = OrderGuardService(DB_PATH)
    flash("Demo data reset.", "info")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
