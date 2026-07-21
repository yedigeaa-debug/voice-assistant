"""CLI for the Almaty voice agent.

Examples
--------
# speak arbitrary text (language auto-detected):
python -m voice_agent --say "Сәлем! Алматыда бүгін ауа райы тамаша." --out hello_kk.wav

# ask with text, get a spoken answer:
python -m voice_agent --ask "What interesting events are there in Almaty?"

# full voice loop (records the mic, answers aloud, repeats):
python -m voice_agent --voice
"""

from __future__ import annotations

import argparse

from .agent import VoiceAgent


def main() -> None:
    p = argparse.ArgumentParser(prog="voice_agent",
                                description="en/ru/kk voice agent for Almaty events")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--say", metavar="TEXT", help="just synthesize TEXT")
    mode.add_argument("--ask", metavar="QUESTION", help="text question -> spoken answer")
    mode.add_argument("--voice", action="store_true", help="microphone conversation loop")
    p.add_argument("--lang", choices=["en", "ru", "kk"], help="force language (default: auto)")
    p.add_argument("--out", help="output wav path")
    p.add_argument("--seconds", type=float, default=6.0, help="mic recording window")
    p.add_argument("--speaker-wav", help="6+ s reference wav to clone a voice")
    p.add_argument("--city", default="almaty", help="sxodim.com city slug")
    p.add_argument("--no-play", action="store_true", help="don't play audio")
    args = p.parse_args()

    agent = VoiceAgent(speaker_wav=args.speaker_wav, city=args.city)
    play = not args.no_play

    if args.say:
        wav = agent.say(args.say, args.lang, args.out)
        print(f"saved: {wav}")
        if play:
            from .agent import play_wav
            play_wav(wav)
    elif args.ask:
        # demo: answer in Russian unless another language is forced via --lang
        agent.ask(args.ask, args.out, play=play, language=args.lang or "ru")
    else:  # --voice
        print("Voice mode — Ctrl+C to quit.")
        try:
            while True:
                agent.voice_turn(seconds=args.seconds, play=play)
                print()
        except KeyboardInterrupt:
            print("\nbye!")


if __name__ == "__main__":
    main()
