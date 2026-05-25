"""Örnek plugin – manifest yapısını gösterir."""

PLUGIN_MANIFEST = {
    "allowed_tools": ["search", "read_file", "write_file"],
    "allowed_paths": ["./storage", "./exports"],
    "allow_network": False,
}


def register(orch):
    """Plugin register fonksiyonu. orch: Orchestrator örneği."""
    # Plugin burada araçları kaydedebilir, hook ekleyebilir.
    pass
