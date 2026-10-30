"""휴대폰 알림(ntfy) 설정 — 구독 이름을 내 설정(~/.config/knowledge-base/config.json 의 ntfy_topic)에 넣고 시험 알림을 보낸다.

  python3 ntfy_setup.py status          # 설정돼 있는지만(있음/없음)
  python3 ntfy_setup.py new             # 남이 못 맞힐 구독 이름을 새로 만들어 저장하고, 휴대폰 앱에 넣을 수 있게 한 번만 보여 준다
  python3 ntfy_setup.py new --force     # 이미 있어도 새로 (옛 구독은 휴대폰 앱에서 지운다)
  python3 ntfy_setup.py set             # 이미 쓰는 구독 이름을 표준 입력으로 받아 저장 (echo 이름 | python3 ntfy_setup.py set)
  python3 ntfy_setup.py test            # 시험 알림 한 건
  python3 ntfy_setup.py off             # 구독 이름 · 토큰 지우기(알림 끔)

구독 이름은 비밀번호처럼 다룬다 — 아는 사람은 누구나 내 휴대폰에 알림을 보낼 수 있다. 「new」 말고는 출력하지 않는다.
"""
import importlib.util, pathlib, re, secrets, sys, urllib.request

_s = importlib.util.spec_from_file_location("kbsettings", pathlib.Path(__file__).resolve().parents[2] / "kb/scripts/settings.py")
S = importlib.util.module_from_spec(_s); _s.loader.exec_module(S)   # 내 설정은 ~/.config/knowledge-base/


def send(topic, title, body, token=""):
    hdr = {"Title": title.encode("utf-8").decode("latin-1"), "Priority": "high", "Tags": "bell"}
    if token:
        hdr["Authorization"] = "Bearer " + token
    req = urllib.request.Request("https://ntfy.sh/" + topic, data=body.encode("utf-8"), headers=hdr, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200, f"HTTP {r.status}"
    except Exception as e:
        return False, str(e).replace(topic, "***")


def main():
    a = sys.argv[1:] or ["status"]
    cmd, force = a[0], "--force" in a
    c = S.load()
    has = bool((c.get("ntfy_topic") or "").strip())

    if cmd == "status":
        print("휴대폰 알림:", "설정됨" if has else "아직 없음", "· 토큰:", "있음" if c.get("ntfy_token") else "없음")
    elif cmd == "new":
        if has and not force:
            print("이미 구독 이름이 있어요. 새로 만들려면 --force (옛 구독은 휴대폰 앱에서 지우기)"); sys.exit(1)
        topic = "kb-" + secrets.token_hex(8)
        c["ntfy_topic"] = topic; S.save(c)
        print("저장했어요. 휴대폰 ntfy 앱에서 아래 이름을 구독하세요(이 화면에서만 한 번 보여 줘요):")
        print(topic)
    elif cmd == "set":
        topic = sys.stdin.read().strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", topic):
            print("구독 이름은 영어 · 숫자 · - · _ 만, 64자까지예요"); sys.exit(1)
        c["ntfy_topic"] = topic; S.save(c)
        print("저장했어요(이름은 다시 보여 주지 않아요)")
    elif cmd == "test":
        if not has:
            print("아직 구독 이름이 없어요 — 먼저 new 또는 set"); sys.exit(1)
        ok, why = send(c["ntfy_topic"].strip(), "알림 시험", "이 알림이 보이면 설정 끝이에요. 아침 브리핑이 여기로 와요.", (c.get("ntfy_token") or "").strip())
        print("시험 알림을 보냈어요 — 휴대폰을 보세요" if ok else "보내기 실패: " + why)
        sys.exit(0 if ok else 1)
    elif cmd == "off":
        c.pop("ntfy_topic", None); c.pop("ntfy_token", None); S.save(c)
        print("휴대폰 알림을 껐어요(구독 이름을 지웠어요)")
    else:
        print(__doc__); sys.exit(1)


if __name__ == "__main__":
    main()
