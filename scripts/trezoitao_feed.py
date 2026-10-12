#!/usr/bin/env python3
"""Mantido por compatibilidade: o feed do Trezoitão agora sai do canal_feed.py (RSS com fallback yt-dlp)."""
import os, sys
os.execv(sys.executable, [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "canal_feed.py"), "UCC-r6vnXtcwBYq0VxZYhoXg", os.path.expanduser("~/radio_audio/trezoitao.json")])
