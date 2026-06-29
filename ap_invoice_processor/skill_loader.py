import os
import re

class SkillRules:
    def __init__(self, auto_post_ceiling: float = 5000.0, min_confidence: float = 0.85, vendor_mappings = None, fallback_keywords = None):
        self.auto_post_ceiling = auto_post_ceiling
        self.min_confidence = min_confidence
        self.vendor_mappings = vendor_mappings or [
            {"keywords": ["amazon web services", "aws", "cloud"], "gl": "6000", "gl_name": "Cloud & Hosting Services", "department": "Engineering"},
            {"keywords": ["staples", "office", "supplies", "paper"], "gl": "6100", "gl_name": "Office Supplies & Software", "department": "Administration"},
            {"keywords": ["apex consulting", "advisory", "consulting"], "gl": "6200", "gl_name": "Professional Services", "department": "Legal & Finance"},
            {"keywords": ["apple", "hardware", "macbook", "computer"], "gl": "7000", "gl_name": "Computer Equipment", "department": "IT Infrastructure"},
            {"keywords": ["acme", "marketing", "ads", "advertising"], "gl": "6500", "gl_name": "Marketing & Advertising", "department": "Marketing"}
        ]
        self.fallback_keywords = fallback_keywords or [
            {"keywords": ["hosting", "server", "cloud"], "gl": "6000", "gl_name": "Cloud & Hosting Services", "department": "Engineering"},
            {"keywords": ["paper", "pen", "desk", "chair"], "gl": "6100", "gl_name": "Office Supplies & Software", "department": "Administration"},
            {"keywords": ["legal", "audit", "advisory"], "gl": "6200", "gl_name": "Professional Services", "department": "Legal & Finance"},
            {"keywords": ["laptop", "monitor", "phone"], "gl": "7000", "gl_name": "Computer Equipment", "department": "IT Infrastructure"}
        ]

def load_skill_rules(skill_file_path: str = None) -> SkillRules:
    if not skill_file_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skill_file_path = os.path.join(base_dir, "skills", "ap_invoice_skill", "SKILL.md")
    
    if not os.path.exists(skill_file_path):
        return SkillRules()

    try:
        with open(skill_file_path, "r") as f:
            content = f.read()
        
        ceiling_match = re.search(r"Auto-Post Ceiling.*?`\$?([\d\.]+)`", content)
        ceiling = float(ceiling_match.group(1)) if ceiling_match else 5000.0

        conf_match = re.search(r"Minimum Confidence Threshold.*?`([\d\.]+)`", content)
        min_conf = float(conf_match.group(1)) if conf_match else 0.85

        # Dynamically parse Markdown table in SKILL.md
        parsed_mappings = []
        table_lines = re.findall(r"^\|(.*)\|$", content, re.MULTILINE)
        for line in table_lines:
            cols = [c.strip().replace("`", "") for c in line.split("|")]
            if len(cols) >= 4 and cols[0] and not cols[0].startswith("-") and not "Vendor Pattern" in cols[0]:
                kws = [k.strip().lower() for k in cols[0].split(",")]
                gl_acc = cols[1]
                gl_name = cols[2]
                dept = cols[3]
                parsed_mappings.append({
                    "keywords": kws,
                    "gl": gl_acc,
                    "gl_name": gl_name,
                    "department": dept
                })

        return SkillRules(
            auto_post_ceiling=ceiling,
            min_confidence=min_conf,
            vendor_mappings=parsed_mappings if parsed_mappings else None
        )
    except Exception as e:
        print(f"Warning loading SKILL.md: {e}. Using standard default rules.")
        return SkillRules()
