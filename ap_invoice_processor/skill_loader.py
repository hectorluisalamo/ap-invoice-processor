import os
import re

class SkillRules:
    def __init__(self, auto_post_ceiling: float = 5000.0, min_confidence: float = 0.85):
        self.auto_post_ceiling = auto_post_ceiling
        self.min_confidence = min_confidence
        self.vendor_mappings = [
            {"keywords": ["amazon web services", "aws", "cloud"], "gl": "6000", "gl_name": "Cloud & Hosting Services", "department": "Engineering"},
            {"keywords": ["staples", "office", "supplies", "paper"], "gl": "6100", "gl_name": "Office Supplies & Software", "department": "Administration"},
            {"keywords": ["apex consulting", "advisory", "consulting"], "gl": "6200", "gl_name": "Professional Services", "department": "Legal & Finance"},
            {"keywords": ["apple", "hardware", "macbook", "computer"], "gl": "7000", "gl_name": "Computer Equipment", "department": "IT Infrastructure"},
            {"keywords": ["acme", "marketing", "ads", "advertising"], "gl": "6500", "gl_name": "Marketing & Advertising", "department": "Marketing"}
        ]
        self.fallback_keywords = [
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

        return SkillRules(auto_post_ceiling=ceiling, min_confidence=min_conf)
    except Exception as e:
        print(f"Warning loading SKILL.md: {e}. Using standard default rules.")
        return SkillRules()
