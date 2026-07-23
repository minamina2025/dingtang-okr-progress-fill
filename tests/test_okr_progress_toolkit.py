import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "okr_progress_toolkit.py"


def load_module():
    spec = importlib.util.spec_from_file_location("okr_progress_toolkit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_sanitize_text_redacts_common_sensitive_values():
    module = load_module()
    text = "薪资：80000 元，绩效分: 3.8，手机 13800138000，mail a@example.com"
    out = module.sanitize_text(text)
    assert "80000" not in out
    assert "3.8" not in out
    assert "13800138000" not in out
    assert "a@example.com" not in out


def test_recruiting_ratio_excludes_previous_quarter_and_counts_onboarded():
    module = load_module()
    rows = [
        {"slotId": "a", "title": "重点岗位A", "status": "招聘中"},
        {"slotId": "b", "title": "重点岗位B", "onboardQuarter": "2026年3季度"},
        {"slotId": "c", "title": "重点岗位C", "offerQuarter": "2026年2季度", "status": "招聘中"},
    ]
    result = module.compute_recruiting_ratio(rows, "2026年3季度")
    assert result["previousPeriod"] == "2026q2"
    assert result["denominator"] == 2
    assert result["numerator"] == 1
    assert result["rate"] == 50.0
    assert len(result["excludedPreviousQuarter"]) == 1


def test_validate_plan_checks_ids_progress_and_note():
    module = load_module()
    okr = {"processed": {"objectives": [{"keyResults": [{"keyResultId": "kr-1"}]}]}}
    good = {"updates": [{"krId": "kr-1", "progress": 20, "note": "已完成阶段推进", "evidence": []}]}
    assert module.validate_plan(good, okr)["ok"]
    bad = {"updates": [{"krId": "kr-x", "progress": 120, "note": ""}]}
    result = module.validate_plan(bad, okr)
    assert not result["ok"]
    assert any("not found" in item for item in result["errors"])


def test_render_markdown_includes_sanitized_note():
    module = load_module()
    plan = {
        "title": "测试",
        "period": "2026年3季度",
        "updates": [
            {
                "krId": "kr-1",
                "label": "O1 KR1",
                "progress": 10,
                "note": "事项推进，薪资：90000 元不展示",
                "evidence": [{"summary": "业务系统截图", "path": "/tmp/a.svg"}],
            }
        ],
    }
    out = module.render_markdown(plan)
    assert "# 测试" in out
    assert "90000" not in out
    assert "/tmp/a.svg" not in out
    assert "待补内嵌截图" in out


def test_validate_presentation_rejects_local_paths_without_embed():
    module = load_module()
    plan = {
        "updates": [
            {
                "krId": "kr-1",
                "label": "O1 KR1",
                "progress": 10,
                "note": "证据见 /Users/example/local.png",
                "evidence": [{"summary": "业务系统截图", "path": "/Users/example/local.png"}],
            }
        ]
    }
    result = module.validate_presentation(plan)
    assert not result["ok"]
    assert any("local path" in item for item in result["errors"])


def test_validate_presentation_allows_embedded_image_and_named_link():
    module = load_module()
    plan = {
        "updates": [
            {
                "krId": "kr-1",
                "label": "O1 KR1",
                "progress": 10,
                "note": "证据已内嵌展示",
                "evidence": [
                    {
                        "summary": "业务系统截图",
                        "path": "/Users/example/local.png",
                        "display": "业务系统Dashboard脱敏快照",
                        "pasteIntoDingteam": True,
                        "presentationStatus": "verified",
                    },
                    {
                        "summary": "Q3文档",
                        "url": "https://alidocs.dingtalk.com/example",
                        "display": "Q3 OKR文档",
                        "dingteamLinkVerified": True,
                    },
                ],
            }
        ]
    }
    result = module.validate_presentation(plan)
    assert result["ok"]


def test_validate_presentation_rejects_path_or_url_as_display_text():
    module = load_module()
    plan = {
        "updates": [
            {
                "krId": "kr-1",
                "label": "O1 KR1",
                "progress": 10,
                "note": "证据已内嵌展示",
                "evidence": [
                    {
                        "summary": "业务系统截图",
                        "path": "/Users/example/local.png",
                        "display": "/Users/example/local.png",
                        "pasteIntoDingteam": True,
                    },
                    {
                        "summary": "Q3文档",
                        "url": "https://alidocs.dingtalk.com/example",
                        "display": "https://alidocs.dingtalk.com/example",
                    },
                ],
            }
        ]
    }
    result = module.validate_presentation(plan)
    assert not result["ok"]
    assert any("readable title" in item for item in result["errors"])


def test_render_markdown_uses_named_link_and_image_caption():
    module = load_module()
    plan = {
        "title": "测试",
        "period": "2026年3季度",
        "updates": [
            {
                "krId": "kr-1",
                "label": "O1 KR1",
                "progress": 10,
                "note": "证据已整理",
                "evidence": [
                    {
                        "summary": "业务系统截图",
                        "path": "/Users/example/local.png",
                        "display": "业务系统Dashboard脱敏快照",
                        "pasteIntoDingteam": True,
                    },
                    {
                        "summary": "Q3文档",
                        "url": "https://alidocs.dingtalk.com/example",
                        "display": "Q3 OKR文档",
                    },
                ],
            }
        ],
    }
    out = module.render_markdown(plan)
    assert "/Users/example/local.png" not in out
    assert "业务系统Dashboard脱敏快照（写回时内嵌图片）" in out
    assert "[Q3 OKR文档](https://alidocs.dingtalk.com/example)" in out
