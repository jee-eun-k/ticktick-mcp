"""Tests for token store."""

from ticktick_mcp.src.token_store import FileTokenStore


class TestFileTokenStore:
    def test_save_and_load(self, tmp_path):
        env_file = tmp_path / ".env"
        store = FileTokenStore(env_file)

        store.save_tokens({"TICKTICK_ACCESS_TOKEN": "abc", "TICKTICK_REFRESH_TOKEN": "xyz"})

        loaded = store.load_tokens()
        assert loaded["TICKTICK_ACCESS_TOKEN"] == "abc"
        assert loaded["TICKTICK_REFRESH_TOKEN"] == "xyz"

    def test_preserves_existing(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TICKTICK_CLIENT_ID=myid\nTICKTICK_CLIENT_SECRET=mysecret\n")

        store = FileTokenStore(env_file)
        store.save_tokens({"TICKTICK_ACCESS_TOKEN": "tok"})

        loaded = store.load_tokens()
        assert loaded["TICKTICK_CLIENT_ID"] == "myid"
        assert loaded["TICKTICK_ACCESS_TOKEN"] == "tok"

    def test_load_empty_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("")
        store = FileTokenStore(env_file)
        assert store.load_tokens() == {}

    def test_load_nonexistent(self, tmp_path):
        store = FileTokenStore(tmp_path / "nonexistent.env")
        assert store.load_tokens() == {}

    def test_skips_comments(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# comment\nKEY=value\n")
        store = FileTokenStore(env_file)
        loaded = store.load_tokens()
        assert "# comment" not in loaded
        assert loaded["KEY"] == "value"
