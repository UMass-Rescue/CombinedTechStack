from PIL import Image
import time
import librosa
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Tokenizer
import IPython.display as display
import soundfile as sf
import truecase
import spacy
from spacy import displacy
from collections import Counter
import en_core_web_sm
import truecase

nlp = spacy.load("en_core_web_sm")
import moviepy.editor as mp


def init():
    """
    This method will be run once on startup. You should check if the supporting files your
    model needs have been created, and if not then you should create/fetch them.
    """
    # Placeholder init code. Replace the sleep with check for model files required etc...
    time.sleep(1)
    global __tokenizer
    __tokenizer = Wav2Vec2Tokenizer.from_pretrained("facebook/wav2vec2-base-960h")
    global __model
    __model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")


def predict(prediction_object_path):
    """
    Interface method between model and server. This signature must not be
    changed and your model must be able to create a prediction from the object
    file that is passed in.

    Depending on the model type as defined in model/config.py, this method will receive a different input:

    'object'  :  Model receives a file name to an image file, opens it, and creates a prediction
    'text'   :  Model receives a string of text and uses it to create a prediction.


    Note: All objects are stored in the directory '/app/objects/' in the Docker container. You may assume that the file
    path that is passed to this method is valid and that the image file exists.

    prediction_object_path will be in the form: "app/objects/file_name", where file_name is the video, image, etc. file.
    """

    video = mp.VideoFileClip('/app/objects/' + prediction_object_path)
    ex_aud = video.audio

    ex_aud.write_audiofile("short1.wav")

    # Loading the audio file
    audio, rate = librosa.load("short1.wav", sr=16000)

    # Importing Wav2Vec pretrained model

    def asr_transcript(tokenizer, model, input_file):
        if not tokenizer:
            print("Not receving tokenizer", flush=True)

        transcript = ""
        pre, rate = librosa.load(input_file, sr=16000)
        sf.write("temp1.wav", pre, rate)
        stream = librosa.stream("temp1.wav",
                                block_length=25,
                                frame_length=16000,
                                hop_length=16000)
        for speech in stream:
            if len(speech.shape) > 1:
                speech = speech[:, 0] + speech[:, 1]
        input_values = tokenizer(speech, return_tensors="pt").input_values
        logits = model(input_values).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = tokenizer.batch_decode(predicted_ids)[0]
        # print(transcription)
        transcript += truecase.get_true_case(transcription.lower())

        return transcript

    short1_trans = asr_transcript(__tokenizer, __model, "short1.wav")

    # file1 = open("speech.txt", "w")
    # file1.write(short1_trans)
    # file = open("speech.txt", mode="r")
    # speech = file.read()
    ner_dict = {'DATE': [], 'PERSON': [], 'GPE': [], 'ORG': [], 'TIME': [], 'LOC': [], 'LANGUAGE': [], 'PRODUCT': [],
                "FAC": []}

    # put the Speech.txt string into the nlp object (this pipeline automatically extracts NER entities)
    doc = nlp(short1_trans)
    for entities in doc.ents:
        if entities.label_ == "CARDINAL":
            nothing = "nothing"
        else:
            # print(f"word: {entities.text}: TAG: {entities.label_}")
            ner_dict[entities.label_].append(entities.text)

    return {
        'classes': ['DATE', 'PERSON', 'GPE', 'ORG', 'TIME', 'LOC', 'LANGUAGE', 'PRODUCT', "FAC"],
        # List every class in the classifier
        'result': ner_dict
    }
