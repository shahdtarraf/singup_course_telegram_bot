from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


# University materials hierarchy
YEARS = [
    {
        "id": 3,
        "name": "السنة الثالثة",
        "semesters": {
            1: [
                {"id": "y3_s1_algo_ds", "name": "خوارزميات وبنى معطيات"},
                {"id": "y3_s1_os1", "name": "نظم تشغيل 1"},
                {"id": "y3_s1_computing", "name": "حوسبة"},
            ],
            2: [
                {"id": "y3_s2_complexity", "name": "تعقيد"},
                {"id": "y3_s2_ai_principles", "name": "مبادئ الذكاء"},
                {"id": "y3_s2_se1", "name": "هندسة برمجيات 1"},
                {"id": "y3_s2_comp_arch1", "name": "بنيان حواسيب 1"},
            ],
        },
    },
    {
        "id": 4,
        "name": "السنة الرابعة (ذكاء)",
        "semesters": {
            1: [
                {"id": "y4_s1_multimedia", "name": "نظم وسائط متعددة"},
                {"id": "y4_s1_concurrent", "name": "برمجة تفرعية"},
                {"id": "y4_s1_nn", "name": "الشبكات العصبونية"},
                {"id": "y4_s1_smart_search", "name": "خوارزميات بحث ذكية"},
            ],
            2: [
                {"id": "y4_s2_compilers", "name": "بناء مترجمات"},
                {"id": "y4_s2_cv", "name": "رؤية حاسوبية"},
                {"id": "y4_s2_project", "name": "مشروع فصلي"},
            ],
        },
    },
    {
        "id": 5,
        "name": "السنة الخامسة",
        "semesters": {
            1: [
                {"id": "y5_s1_prob_logic", "name": "منطق ترجيحي"},
            ],
            2: [
                {"id": "y5_s2_nlp", "name": "معالجة اللغات الطبيعية"},
                {"id": "y5_s2_kd", "name": "استكشاف معرفة"},
                {"id": "y5_s2_rl", "name": "تعلم معزز"},
            ],
        },
    },
]


def material_details(material_id: str) -> Dict:
    # Shared template for material content
    base = {
        "teacher": "المهندسة شهد طراف",
        "program": [
            "متابعة موادهم الجامعية بشكل منظّم خلال الفصل الدراسي.",
            "عرض الملخصات لكل مادة.",
            "اختبارات قصيرة بعد كل محاضرة.",
            "تدريب عملي على أسئلة سابقة.",
            "تقييم دوري لمستوى التقدم الأكاديمي لكل طالب.",
        ],
        "price": 50000,
    }
    # Display name lookup from YEARS
    for y in YEARS:
        for sem, mats in y["semesters"].items():
            for m in mats:
                if m["id"] == material_id:
                    return {
                        "id": material_id,
                        "name": m["name"],
                        **base,
                    }
    # fallback
    return {
        "id": material_id,
        "name": material_id,
        **base,
    }


# Professional courses
COURSES = [
    {
        "id": "nlp_beginner",
        "name": "معالجة اللغات الطبيعية - مبتدئ",
        "duration": "6 أشهر",
        "price": 75000,
        "content": [
            "أساسيات الرياضيات",
            "Python",
            "تعلم الآلة (Machine Learning)",
            "التعلم العميق (Deep Learning)",
            "معالجة اللغات الطبيعية (NLP)",
        ],
        "projects": [
            "نظام توصيات أفلام",
            "تحليل المشاعر",
            "تصميم شات بوت ذكي",
        ],
    },
    {
        "id": "nlp_intermediate",
        "name": "معالجة اللغات الطبيعية - متوسط",
        "duration": "3 أشهر",
        "price": 75000,
        "content": [
            "تعلم الآلة (Machine Learning)",
            "التعلم العميق (Deep Learning)",
            "معالجة اللغات الطبيعية (NLP)",
        ],
        "projects": [
            "نظام توصيات أفلام",
            "تحليل المشاعر",
            "تصميم شات بوت ذكي",
        ],
    },
    {
        "id": "nlp_expert",
        "name": "معالجة اللغات الطبيعية - خبير",
        "duration": "شهر",
        "price": 75000,
        "content": [
            "تطبيقات متقدمة في NLP",
        ],
        "projects": [
            "تصميم شات بوت ذكي قادر على التفاعل مع المستخدم",
        ],
    },
]


def get_course(cid: str) -> Optional[Dict]:
    return next((c for c in COURSES if c["id"] == cid), None)
