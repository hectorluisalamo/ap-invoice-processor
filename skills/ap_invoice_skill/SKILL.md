---
name: ap-invoice-skill
description: Portable agent skill for accounts payable invoice processing, GL account coding, vendor matching, and policy threshold validation.
version: 1.0.0
---

# Accounts Payable Agent Skill

This skill defines company accounting policies, vendor-to-GL account mappings, and automated approval safety rails for AP processing.

## 1. Safety Rails & Approval Thresholds

- **Hard Auto-Post Ceiling**: `$5000.00`
  - Any invoice with a total amount **greater than or equal to $5000.00** MUST be routed to the Human Gate for explicit approval, even if all other validations pass.
- **Minimum Confidence Threshold**: `0.85`
  - If any critical extracted field (vendor, invoice number, date, total amount) has a confidence score below `0.85`, route to Human Gate.
- **PO Enforcement**:
  - For vendors requiring a PO (`po_required = true`), the PO number must exist in the PO database. Additionally, any PO number supplied on an invoice — even for a vendor that does not require one — is validated against the database. Mismatched or missing POs route to Human Gate.
- **Unknown Vendor**:
  - If the invoice vendor cannot be matched to an entry in the vendor master (by name or alias), route to the Human Gate. An unrecognized payee is treated as high-risk and never auto-posted.
- **Duplicate Prevention**:
  - Invoices with an invoice number matching any historically posted entry route to Human Gate as suspected duplicates.

## 2. Vendor to GL Account Mapping Rules

| Vendor Pattern / Keywords | GL Account | GL Account Name | Department |
|---|---|---|---|
| `Amazon Web Services`, `AWS`, `Cloud` | `6000` | Cloud & Hosting Services | Engineering |
| `Staples`, `Office`, `Supplies`, `Paper` | `6100` | Office Supplies & Software | Administration |
| `Apex Consulting`, `Advisory`, `Consulting` | `6200` | Professional Services | Legal & Finance |
| `Apple`, `Hardware`, `MacBook`, `Computer` | `7000` | Computer Equipment | IT Infrastructure |
| `Acme`, `Marketing`, `Ads`, `Advertising` | `6500` | Marketing & Advertising | Marketing |

## 3. Fallback GL Coding Rules

If an invoice line item vendor is unknown or unlisted in vendor master:
- Search line item description for keywords:
  - `"hosting"`, `"server"`, `"cloud"` -> `6000` (Engineering)
  - `"paper"`, `"pen"`, `"desk"`, `"chair"` -> `6100` (Administration)
  - `"legal"`, `"audit"`, `"advisory"` -> `6200` (Legal & Finance)
  - `"laptop"`, `"monitor"`, `"phone"` -> `7000` (IT Infrastructure)
- If no keyword match, assign default fallback GL `6100` with low confidence flag.
