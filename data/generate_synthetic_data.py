import json
import os
import random
from datetime import datetime, timedelta

def generate_synthetic_dataset(num_invoices: int = 50):
    # Seed so regeneration is deterministic/reproducible (the committed dataset
    # predates this seed and is intentionally NOT regenerated here).
    random.seed(42)
    data_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(data_dir, "synthetic_invoices")
    os.makedirs(output_dir, exist_ok=True)

    # Valid PO database for matching checks
    valid_pos = {
        f"PO-88{i:02d}": {
            "vendor_id": f"VEND-100{(i%5)+1}",
            "amount": round(random.uniform(200, 4800), 2)
        } for i in range(1, 30)
    }
    with open(os.path.join(data_dir, "po_database.json"), "w") as f:
        json.dump(valid_pos, f, indent=2)

    # Historical posted invoice numbers for duplicate checks
    historical_invoices = [f"INV-HIST-{9000+i}" for i in range(20)]
    with open(os.path.join(data_dir, "historical_invoices.json"), "w") as f:
        json.dump(historical_invoices, f, indent=2)

    # Derive vendors from the canonical vendor_master.json so a generated invoice can
    # never display an alias the agent doesn't know. Previously this list was hand-kept
    # in parallel and drifted (e.g. "Apple Store" here vs "Apple Store for Business" in
    # the master), which mismatched the substring matcher and produced spurious
    # unknown_vendor routes that unfairly scored the agent down.
    with open(os.path.join(data_dir, "vendor_master.json")) as f:
        vendor_master = json.load(f)
    vendors = [
        {
            "id": vm["vendor_id"],
            "name": vm["name"],
            "aliases": vm.get("aliases", []),
            "gl": vm["default_gl_account"],
            "po_req": vm.get("po_required", False),
        }
        for vm in vendor_master
    ]

    invoices = []
    po_keys = list(valid_pos.keys())

    for idx in range(1, num_invoices + 1):
        inv_id = f"INV-2026-{idx:03d}"
        v_info = random.choice(vendors)
        
        # Determine scenario type
        rand_val = random.random()
        if rand_val < 0.55:
            scenario = "clean_auto_post"
        elif rand_val < 0.70:
            scenario = "high_dollar_ceiling"
        elif rand_val < 0.80:
            scenario = "po_mismatch"
        elif rand_val < 0.90:
            scenario = "duplicate_invoice"
        else:
            scenario = "low_confidence"

        if scenario == "high_dollar_ceiling":
            total_amount = round(random.uniform(5200.0, 12500.0), 2)
        else:
            total_amount = round(random.uniform(150.0, 4800.0), 2)

        if scenario == "duplicate_invoice":
            invoice_num = random.choice(historical_invoices)
        else:
            invoice_num = inv_id

        if scenario == "po_mismatch":
            po_num = "PO-9999-INVALID"
        elif v_info["po_req"] or random.random() > 0.5:
            po_num = random.choice(po_keys)
        else:
            po_num = None

        vendor_disp_name = random.choice(v_info["aliases"]) if random.random() > 0.4 else v_info["name"]
        
        if scenario == "low_confidence":
            conf_score = round(random.uniform(0.55, 0.78), 2)
        else:
            conf_score = round(random.uniform(0.92, 0.99), 2)

        # Build line items that sum EXACTLY to total_amount (the last item absorbs the
        # rounding remainder), preserving the scenario's intended total. The previous
        # version re-divided each item and then overwrote total_amount with the smaller
        # sum, which could drop a high_dollar_ceiling invoice below $5k and silently
        # mislabel it as auto_post-eligible.
        line_qty = random.randint(1, 3)
        base = round(total_amount / line_qty, 2)
        line_items = []
        running = 0.0
        for i in range(line_qty):
            amt = round(total_amount - running, 2) if i == line_qty - 1 else base
            running += amt
            line_items.append({
                "description": f"{v_info['name']} Service / Product Item #{i+1}",
                "qty": 1,
                "unit_price": amt,
                "amount": amt
            })

        expected_route = "auto_post" if scenario == "clean_auto_post" else "human_review"

        raw_text = f"INVOICE #{invoice_num}\nVendor: {vendor_disp_name}\nDate: 2026-06-28\nPO: {po_num or 'N/A'}\nTotal: ${total_amount:.2f}"

        invoices.append({
            "id": inv_id,
            "test_case_type": scenario,
            "description": f"Synthetic scenario: {scenario}",
            "raw_text": raw_text,
            "ground_truth": {
                "vendor_name": v_info["name"],
                "vendor_id": v_info["id"],
                "invoice_number": invoice_num,
                "date": "2026-06-28",
                "po_number": po_num,
                "total_amount": total_amount,
                "expected_route": expected_route,
                "expected_gl": v_info["gl"],
                "line_items": line_items
            },
            "simulated_extraction": {
                "vendor_name": vendor_disp_name if scenario != "low_confidence" else "Unknown Entity",
                "invoice_number": invoice_num,
                "date": "2026-06-28",
                "po_number": po_num,
                "total_amount": total_amount,
                "line_items": line_items,
                "confidence": {
                    "vendor_name": conf_score,
                    "invoice_number": conf_score,
                    "date": conf_score,
                    "total_amount": conf_score,
                    "line_items": conf_score
                }
            }
        })

    with open(os.path.join(output_dir, "invoices.json"), "w") as f:
        json.dump(invoices, f, indent=2)

    print(f"Successfully generated expanded synthetic dataset with {num_invoices} invoices in {output_dir}")

if __name__ == "__main__":
    generate_synthetic_dataset(50)
