from pydub import AudioSegment

audio = AudioSegment.from_file("soy_luis.ogg")

print(f"Duration {len(audio)}")
print(f"Sample rate {audio.frame_rate}")
print(f"Duration in seconds {audio.duration_seconds}")

silence = AudioSegment.silent(duration=2000)

first_part = audio[:650]
second_part = audio[651:]

output = first_part + silence + second_part
output.export("output.ogg", format="ogg")
