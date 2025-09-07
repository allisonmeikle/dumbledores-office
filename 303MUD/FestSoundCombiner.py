import wave
import struct

####### FUNFEST PROJECT ########
# William and Cagatay, group 23
# this is the code that takes a fest message as input, and renders both instrument
# (through parse) and the final file through "render".
# As recommended by the professor, we render the audio on the client side
# to mitigate download latency.
# This section ended up being less graceful due to the fact that messages needed to be
# JSON serialized, thus polymorphism had to be approximated through a separate field.

# also there should be no errors with the module wav, since it's packaged with python3

FRAMERATE = 44100
SAMPLE_LENGTH = 2 * FRAMERATE

## can be overridden in case we decide to do theme changes.
def get_timed_sequence(num) -> list[int]:
    """The purpose of this function is to add rhythm to a sequence of numbers
    For even numbers, each note is the same length.
    For odd numbers, quarter notes (or notes of 1/8th the sample's length) are played, until one note is left,
    which takes up the rest of the measure.

    :param num:
    :returns list of lengths which each note should be held.:
    """

    if num & 2:
        return [SAMPLE_LENGTH // num] * num
    else:
        temp = [FRAMERATE / 4] * num
        temp.append((SAMPLE_LENGTH // 8) * (8 - num))
        return temp

def parse(message) -> str:
    """
    First round of rendering, renders instrument loop.

    Specifications of instrument loop wav source file:
    16bit mono, >16 sec long. Each note is played for two seconds in an ascending scale.

    :param instrument message:
    :returns path of rendered file:

    """
    ## probably wouldn't make sense to redefine the message data structure here so remember indexes:
    ## 0 -> type. 1 -> id. 2 -> path. 3-> sequence

    timed_sequence = get_timed_sequence(len(message[3])-1)

    with wave.open("rsrc_cache/" +message[2], "rb") as sample, wave.open("rsrc_cache/sound/fest/"+ message[1] + ".wav", "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(FRAMERATE)

        print(timed_sequence)

        for i in range(len(timed_sequence)):
            sample.setpos((2 * FRAMERATE * (int(message[3][i]) - 1)))
            output.writeframes(sample.readframes(int(timed_sequence[i])))

    return "fest/" + message[1] + ".wav"

def render(message: dict):
    """
    Final render pass. Current mixing policy: divide by message length

    :param Fest message:
    :return void. note automatically renders to output.wav:
    """

    ## get files
    amplitudes = [0] * SAMPLE_LENGTH

    print(message)

    for i in range(int(message['len'])):
        path = ""
        submessage = message[str(i)].split(",")

        try:
            print(submessage)
            if submessage[0] == "instrument" and len(submessage[3]) > 0:
                print(submessage[3])
                path = parse(submessage)
                path = "rsrc_cache/sound/" + path
            elif submessage[0] == "loop":
                path = submessage[2]
                path = "rsrc_cache/" + path

            with wave.open(path, 'rb') as current:
                ## if instro -> render and return. if loop -> return path

                cur_frame = struct.unpack("<" + "h" * SAMPLE_LENGTH, current.readframes(SAMPLE_LENGTH))
                amplitudes = [pair[0] + (pair[1] / int(message['len'])) for pair in zip(amplitudes, cur_frame)]

            max_val = max(abs(sample) for sample in amplitudes)
            if max_val > 32767:
                amplitudes = [int(sample * 32767 / max_val) for sample in amplitudes]

        except FileNotFoundError:
            ## send message back
            print("Files Not found:", path)
            ## can call getsound if this is in the client.
            pass


    packed_frames = [struct.pack("<h", int(sample)) for sample in amplitudes]

    with wave.open("rsrc_cache/sound/fest/output.wav", mode="wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(FRAMERATE)

        output.writeframes(b''.join(packed_frames))