"""从 transcript.json 生成带真实总结与话题小节的成稿 Markdown（供检阅；总结与摘要由规则/模板或外部填入）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from bilibili_transcript.text_post import sanitize_filename_title


def _fmt_ts(seconds: float) -> str:
    s = max(0.0, float(seconds))
    m = int(s // 60)
    sec = int(s % 60)
    return f"{m:02d}:{sec:02d}"


def split_segments_into_n_buckets(
    segments: Sequence[Dict[str, Any]],
    n: int,
) -> List[List[Dict[str, Any]]]:
    """按分段序号均分，保证不在 segment 中间切断。"""
    segs = list(segments)
    if not segs or n < 1:
        return []
    L = len(segs)
    per = (L + n - 1) // n
    buckets: List[List[Dict[str, Any]]] = []
    for i in range(0, L, per):
        buckets.append(segs[i : i + per])
    return buckets[:n] if len(buckets) > n else buckets


def build_eval_markdown(
    *,
    title: str,
    full_summary: str,
    section_main_num: int,
    subsections: List[Tuple[str, str, str]],
) -> str:
    """
    subsections: [(heading, blurb_multiline, body_verbatim), ...]
    blurb_multiline: 段前摘要，可含换行，会按行加 >
    """
    lines: List[str] = []
    lines.append(f"# {title.strip()}")
    lines.append("")
    lines.append("## 全文总结")
    lines.append("")
    for para in full_summary.strip().split("\n\n"):
        para = para.strip()
        if para:
            lines.append(para)
            lines.append("")
    lines.append(f"## {section_main_num}. 完整逐字稿")
    lines.append("")
    for h, blurb, body in subsections:
        lines.append(f"### {h}")
        lines.append("")
        for bl in blurb.strip().split("\n"):
            bl = bl.strip()
            if bl:
                lines.append(f"> {bl}")
        lines.append("")
        lines.append(body.strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def default_subsection_titles_bv1f3() -> List[str]:
    """BV1f3DYBDE9h 单人评述稿的话题标题（与内容对齐）。"""
    return [
        "1.1 开场：别在「谎言」里放弃思考",
        "1.2 「一人公司」热潮与创业赌博本质",
        "1.3 数据与案例：AI创业失败率、工具泡沫与法律业警示",
        "1.4 第二宗罪：把新工具当成商业规律本身",
        "1.5 历史与当下：从个体户到灵活就业，第三宗罪与收束",
    ]


def default_blurbs_bv1f3() -> List[str]:
    return [
        "点题：不能因环境话术放弃思考；各地推动「一人公司」叙事，把联机个体包装成「超级个体」「AI新势力」，本质是泡沫与话术。",
        "拆解「一人公司」= AI创业 × 小规模创业；创业成功概率极低。引出美国 AI 创业失败率、存活期、工具站大量死亡等数据，并对比中国「小微企业」语境。",
        "以 Legalman（口播转写）为例：客户不愿把身家性命交给黑箱大模型；若解决伪需求，市场不会买单；工具普及使「有想法」毫无壁垒，赛道易被大厂功能更新秒杀。",
        "批判「超级个体」Rename：仍是线性业务的个体户；第二宗罪是混淆工具与商业规律。转入历史线：1979、1992、2014 大众创业、2020 灵活就业与地摊经济。",
        "收束：政府/园区叙事与「首次创业」人群结构；指出多数人的折腾对金字塔的燃料意义；点出第三宗罪：失败经验除短视频外价值寥寥；结尾问句收束。",
    ]


def default_subsection_titles_bv1ij() -> List[str]:
    """BV1ijE4zwEHP 李录课堂实录（英文）分节标题（译后呈现）。"""
    return [
        "1.1 一页纸与 Value Line：从「市值」而非「每股」看公司",
        "1.2 课堂互动：韩国案例算市值、盈利与账面",
        "1.3 拆解账面：现金、证券、酒店与百货股权的低估",
        "1.4 安全边际：多重因素与本地市场、散户情绪",
        "1.5 结尾：价值投资的回报、课堂与行动",
    ]


def default_blurbs_bv1ij() -> List[str]:
    return [
        "从一页公司摘要切入，强调「像股东一样思考」：先看市值；介绍各国券商手册与 Value Line 的用途。",
        "以韩国公司为例现场算账：股价、股本、市值、税前盈利与账面价值，批评「不做作业」就无法做投资。",
        "继续拆解资产负债表：流动资产、现金与证券、固定资产、商誉；发现酒店、百货持股等账面低估。",
        "讨论「便宜」是否足够：需核对盈利质量、资产构成、诉讼风险、本地市场与内部人持股比例等。",
        "以股价走势与巴菲特/芒格等为例，强调价值投资可赚钱，但必须亲自做功课；收束于对课堂与学费的感慨与行动呼吁。",
    ]


def _full_summary_bv1ij() -> str:
    return """本视频为李录在哥伦比亚商学院课堂上的**英文讲授实录**（素材为 ASR），核心是用**价值投资者视角**演示：拿到一页公司信息时，如何在几分钟内建立对「市值—盈利—资产结构」的整体把握，并进一步追问「是否便宜」「便宜是否可投」。

**方法线索**：强调不要停留在「每股数据」，而以**市值**与**股东/所有者**思维出发；结合美国券商手册、Value Line 等工具，对比不同国家信息披露差异。

**案例主线**：以韩国某公司为课堂演练对象，现场推算市值、盈利、账面价值与资产构成（现金、证券、酒店、百货股权等），指出账面价值与市场价值之间的裂口，并讨论「便宜」背后的多重风险与信息：诉讼、行业属性、本地投资者结构、内部人持股等。

**投资哲学收束**：呼应巴菲特、芒格传统，强调价值投资路径上「能赚到钱」，但前提是**大量阅读与独立计算**；结尾对商学院学生「不做作业」提出尖锐批评，并以自身经历说明课堂与训练的投资回报。

*说明：口播为英文；专名与数字请以原视频为准；ASR 可能存在漏字与同音误差。英文 ASR 若需中文成稿，请在 Cursor 对话中由助手翻译——流水线不调用任何外部翻译 API。*"""


def _full_summary_bv1f3() -> str:
    return """本视频为博主「波通」的独播评述，围绕「一人公司」这一热词展开，核心论点是：地方与舆论把「一人公司」包装成「超级个体」「AI新势力」，本质是违背商业规律的泡沫与话术；**创业仍是创业**，成功概率极低，与是否冠以 AI 无关。

**论据与数据层面**：视频引用美国 AI 创业公司失败率、平均存活期、AI 工具平台上大量死亡与工具同质化等事实，指出多数「AI 工具」由小团队开发，赛道极易被大厂一次功能更新或同质化竞争清空；在中国语境下，以「小微企业」类比，强调现金流与生存压力——相当比例企业现金流撑不过数月，且对「还能活下去」的信心不足。

**案例层面**：以「法律业」类公司（口播转写为 Legalman）等为例，说明客户对「黑箱大模型」处理关键事务的拒绝；若技术解决的是伪需求或不存在的问题，市场不会给正向反馈。

**概念批判**：视频提出「第二宗罪」——用新工具混淆商业规律；把「个体户/自由职业者」换名为「超级个体」属于误导。随后插入历史脉络：1979 个体户、1992 下海、2014 大众创业、2020 灵活就业与地摊经济等，说明社会在无法提供足够体面岗位时，会反复动员「自主灵活就业」叙事。

**收束**：指出多数「一人公司」创始者为首次创业、年轻学生与大厂离职者等结构；对普通人而言，参与创业浪潮往往成为金字塔底座的「燃料」，失败经验难以沉淀为有效资产；**第三宗罪**即把残酷现实包装成可复制的成功学；结尾以「今天你想通了吗」收束。以上总结以 ASR 转写为据，专名与数字以口播为准，可能存在同音转写误差。"""


def write_eval_markdown_from_json(json_path: Path, out_path: Optional[Path] = None) -> Path:
    """
    从 *_transcript.json 生成**初版**成稿 Markdown：结构 + 分桶时间 + 原文拼接。

    逐字正文为 **segments 文本直接拼接**，不经脚本润色；终稿须由 Cursor 子 Agent 按 Skill
    去口癖、标点、分段、换行（及英译中若需要）。BV1f3DYBDE9h 等使用内嵌总结与分节摘要模板。
    """
    data = json.loads(json_path.read_text(encoding="utf-8"))
    title = data.get("title") or data.get("bvid") or "标题"
    segs = data.get("segments") or []
    if not segs:
        raise ValueError("无 segments")

    bvid = data.get("bvid") or "out"
    n = 5
    buckets = split_segments_into_n_buckets(segs, n)

    if bvid == "BV1f3DYBDE9h":
        headings = default_subsection_titles_bv1f3()
        blurbs = default_blurbs_bv1f3()
        full_summary = _full_summary_bv1f3()
    elif bvid == "BV1ijE4zwEHP":
        headings = default_subsection_titles_bv1ij()
        blurbs = default_blurbs_bv1ij()
        full_summary = _full_summary_bv1ij()
    else:
        headings = [f"1.{i+1} 第{i+1}部分" for i in range(len(buckets))]
        blurbs = [""] * len(buckets)
        raw = (data.get("text") or "")[:1500]
        full_summary = (
            "**【自动占位】以下为正文前约 1500 字摘抄，请替换为规范「全文总结」：**\n\n"
            + raw
            + ("\n……\n" if len(data.get("text") or "") > 1500 else "\n")
        )

    subsections: List[Tuple[str, str, str]] = []
    for i, b in enumerate(buckets):
        h = headings[i] if i < len(headings) else f"1.{i+1} 段落"
        t0, t1 = b[0]["start"], b[-1]["end"]
        extra = blurbs[i] if i < len(blurbs) else ""
        blurb = f"（时间参考：{_fmt_ts(t0)}–{_fmt_ts(t1)}）\n{extra.strip()}"
        # 逐字正文为 segment 原文拼接；标点、分段、去口癖等由 Cursor 子 Agent 终稿覆盖，不用脚本改写。
        body = "".join(s.get("text") or "" for s in b)

        subsections.append((h, blurb, body))

    md = build_eval_markdown(
        title=title,
        full_summary=full_summary,
        section_main_num=1,
        subsections=subsections,
    )

    slug = sanitize_filename_title(title)
    out = out_path or (json_path.parent / f"{slug}_{bvid}_transcript_成稿.md")
    out.write_text(md, encoding="utf-8")
    return out
