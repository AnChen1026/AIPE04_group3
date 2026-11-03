"""Recompile the curated piano catalog without changing course/teacher identities.

python -m scripts.build_demo_catalog --input <catalog.json> --output <catalog.json>
The authored curriculum is versioned separately from stable source identities.
"""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from scripts.demo_catalog import GOALS, LEVELS, course_description

DATA = Path(__file__).parent / "data"
METHODS = [
    ("對比聆聽", "先錄下原有彈法，再比較兩種處理；用聽得見的差異決定修改方向"),
    ("分層組合", "將旋律、低音與其他材料分開確認，再逐層加入；每次只增加一項任務"),
    ("提問與實作", "先說明對音樂的判斷，再用鍵盤驗證；保留試彈與修正前後的紀錄"),
    ("短段精練", "把困難位置拆成短句，設定可完成的速度；能連續做對後才接回前後樂句"),
    ("情境模擬", "以實際演奏情境練習起奏、接續與收尾，再回頭處理最影響完整性的細節"),
    ("譜面與聽覺交叉", "先在譜上標記關鍵材料，再唱奏或拍擊驗證，最後回到完整演奏"),
]
PRACTICE = {
    "intro": "每次 8–12 分鐘起步，先複習再加一個任務",
    "beginner": "每週約 4 次、每次 15–25 分鐘，分段後接回完整短曲",
    "intermediate": "每週約 4–5 次、每次 25–40 分鐘，以錄音和譜面追蹤修正",
    "advanced": "需固定練習，分開安排技術、分析與完整演奏；依曲目調整練習量",
}
SURNAMES = list("林陳張李王吳劉蔡楊許鄭謝郭洪邱曾廖賴徐周葉蘇莊呂江何蕭羅高潘簡朱游彭鍾胡施沈余趙盧梁顏柯孫黃温戴宋方杜丁姚傅程范汪唐馮石董")
# Use a curated name once per teacher, rather than repeating a small set
# for every surname. Stable ordering keeps rebuilds reproducible.
GIVEN = """
品妤 柏宇 雅涵 承恩 以安 思穎 宥廷 芷晴 冠霖 昀庭 婉甄 子恆
怡君 志宏 佳蓉 宗翰 惠雯 建廷 詠心 敬文 淑芬 明哲 玉玲 俊傑
淳雅 立群 采潔 彥廷 靜宜 世傑 美玲 維軒 馨予 孟軒 佩珊 祐誠
若彤 智凱 韻如 致遠 曉雯 博翔 筱筑 季謙 文琪 振宇 姵瑜 宏毅
婉婷 子謙 敏慧 逸凡 芸萱 昱辰 湘芸 家豪 玟伶 定邦 心怡 琮凱
郁婷 景皓 芳瑜 紹文 依庭 允哲 苡晴 辰恩 姿吟 秉修 秀娟 哲安
佳穎 宥均 昕妍 德威 怡萱 澤宇 羽柔 瑞麟 亭妤 昶佑 雅雯 昊倫
映潔 尚恩 雨珊 亦辰 慧如 柏翰 沛蓉 廷軒 郁涵 奕翔 婕妤 宇恆
欣儀 仲祺 思潔 信宏 柔安 皓鈞 芷涵 祈安 佑寧 璟文 憶如 允中
宜珊 庭瑞 詠晴 維仁 宛臻 晉安 瑾瑜 睿哲 瀞文 仁傑 芸甄 震遠
韻竹 克勤 蕙如 敦堯 佳璇 耀文 昭君 知遠 瑋庭 靖堯 婉如 東霖
念慈 友誠 曼甯 恆毅 淑惠 昱丞 祐綺 育誠 雅筑 俊毅 沁儀 寬佑
秋月 永和 芳宜 學謙 惠玲 旭東 佳音 遠志 令儀 崇恩 采薇 南星
佩儀 伯鈞 素華 廷岳 鈺涵 源皓 書妍 冠廷 毓珊 澄宇 蘊如 行之
婧怡 皓然 安琪 希文 詠絮 宸安 莉雯 喬安 悅寧 靖雅 芳華 晏如
""".split()
ENGLISH = """
Emily Jason Sophie Ryan Chloe Daniel Alice Kevin Emma Leo Ivy Lucas
Grace Ethan Claire Eric Olivia Sean Natalie David Audrey Simon Julia Aaron
Wendy Oscar Vivian Henry Stella Brian Fiona Felix Iris Ian Rachel Owen
Tina Patrick Zoe Victor Hannah Adrian Joyce Marcus Cindy Edward Nicole Colin
Amber Evan Hazel Justin Vera Louis Nora Thomas
""".split()


def compile_catalog(source, curriculum):
    """Return a deterministic editorial revision; input records are not mutated."""
    result = json.loads(json.dumps(source))
    by_teacher = defaultdict(list)
    for course in result["courses"]:
        by_teacher[course["public_teacher_id"] or course["teacher_id"]].append(course)
    original_teachers = {t["id"]: t for t in result["teachers"]}
    teacher_keys = list(original_teachers) + [k for k in by_teacher if k not in original_teachers]
    themes = {level: [t for t in curriculum if t["level"] == level] for level in LEVELS}
    teachers = []
    for index, key in enumerate(teacher_keys):
        level = list(LEVELS)[index % 4]
        topic = themes[level][(index // 4) % 20]
        offset = (index // 80) * 2
        method_name, method = METHODS[(index // 4 + index // 80) % len(METHODS)]
        surname = SURNAMES[index % len(SURNAMES)]
        name = (
            f"{ENGLISH[index // 4]} {surname}老師"
            if index % 4 == 3
            else f"{surname}{GIVEN[index - index // 4]}老師"
        )
        selected = []
        for number, course in enumerate(by_teacher[key]):
            lesson = topic["lessons"][offset + number]
            selected.append(lesson)
            mode = course["delivery_mode"]
            if mode == "online":
                setup = "線上一對一；自備鋼琴或數位鋼琴，鏡頭可見雙手。合作題材採分開錄音或老師示範"
                location_type = "online"
            elif mode == "hybrid":
                setup = f"可採線上一對一，或於{course['area']}工作室上課；線上自備樂器，合作排練採實體"
                location_type = "studio_or_online"
            elif (index // 3) % 3 == 0:
                setup = f"{course['area']}到府一對一家教；家中需有鋼琴或數位鋼琴，交通範圍先洽談"
                location_type = "home_visit"
            else:
                setup = f"{course['area']}工作室實體一對一，提供課堂用琴；合作題材的夥伴安排先確認"
                location_type = "studio"
            course.update(
                teacher_name=name, studio_name=f"{name.replace('老師', '').strip()}鋼琴工作室",
                title=lesson["title"], level=level, audience=topic["audience"],
                goals=topic["goals"], style="、".join([topic["theme"], *(GOALS[g] for g in topic["goals"])]),
                description=f"{lesson['task']}。這門{topic['theme']}課程適合{topic['learners']}，以「{lesson['title']}」為明確學習主題。",
                teaching_profile="\n".join([
                    f"先備能力：{topic['prerequisite']}。",
                    f"課堂重點：{lesson['task']}。教法採{method_name}，以課堂試彈確認。",
                    f"練習安排：{PRACTICE[level]}。",
                    f"成果檢核：{lesson['task'].split('，')[-1]}；保留前後對照的演奏或實作紀錄。",
                    f"授課安排：{setup}。教材與曲目版本課前確認。",
                ]),
                curriculum_key=topic["key"], lesson_index=offset + number,
                location_type=location_type,
            )
            assert len(course_description(course)) <= 2000
        original = original_teachers.get(key, {})
        intro = f"以{topic['theme']}為教學重點，主要陪伴{topic['learners']}。採{method_name}，本期著重{selected[0]['task']}。"
        assert len(intro) <= 200
        teachers.append({
            "id": key, "studio_id": original.get("studio_id", by_teacher[key][0]["studio_id"]),
            "display_name": name, "biography": intro, "teaching_style": f"{method_name}：{method}。",
            "specialties": [topic["theme"], *(l["title"] for l in selected)],
            "years_experience": original.get("years_experience"),
            "target_learning": topic["learners"], "curriculum_key": topic["key"],
            "active": True, "is_demo": True,
            "valid_until": original.get("valid_until", by_teacher[key][0]["valid_until"]),
        })
    result["teachers"] = teachers
    assert len({c["title"] for c in result["courses"]}) == 426
    assert len({t["display_name"] for t in teachers}) == 226
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DATA / "aicourse-demo.json")
    parser.add_argument("--output", type=Path, default=DATA / "aicourse-demo.json")
    args = parser.parse_args()
    source = json.loads(args.input.read_text())
    curriculum = json.loads((DATA / "piano-curriculum.json").read_text())
    result = compile_catalog(source, curriculum)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "courses": len(result["courses"]), "teachers": len(result["teachers"]),
        "themes": len({c["curriculum_key"] for c in result["courses"]}),
        "levels": dict(Counter(c["level"] for c in result["courses"])),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
