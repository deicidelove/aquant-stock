from aquant import llm


def test_chat_uses_ollama_when_configured(monkeypatch):
    monkeypatch.setenv("AQUANT_OLLAMA_MODEL", "qwen2.5:7b")
    monkeypatch.setattr(llm, "_ollama_generate", lambda prompt, model, timeout: "OLLAMA回复")
    # claude 不应被调用
    monkeypatch.setattr(llm, "_ask", lambda p: (_ for _ in ()).throw(AssertionError("不该调claude")))
    assert llm.chat("hi") == "OLLAMA回复"


def test_chat_falls_back_to_claude(monkeypatch):
    monkeypatch.delenv("AQUANT_OLLAMA_MODEL", raising=False)
    monkeypatch.setattr(llm, "_ask", lambda p: "CLAUDE回复")
    assert llm.chat("hi") == "CLAUDE回复"


def test_chat_ollama_error_falls_back(monkeypatch):
    monkeypatch.setenv("AQUANT_OLLAMA_MODEL", "qwen2.5:7b")
    monkeypatch.setattr(llm, "_ollama_generate",
                        lambda prompt, model, timeout: (_ for _ in ()).throw(OSError("down")))
    monkeypatch.setattr(llm, "_ask", lambda p: "CLAUDE兜底")
    assert llm.chat("hi") == "CLAUDE兜底"


def test_chat_none_when_nothing(monkeypatch):
    monkeypatch.delenv("AQUANT_OLLAMA_MODEL", raising=False)
    monkeypatch.setattr(llm, "_ask", lambda p: None)
    assert llm.chat("hi") is None
