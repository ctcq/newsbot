import logging
import json
import speech_recognition as sr
import subprocess

DEEPSPEECH_MODEL_DIRECTORY = '/opt/deepspeech/'
DEEPSPEECH_MODEL = DEEPSPEECH_MODEL_DIRECTORY + 'deepspeech-0.7.0-models.pbmm'
DEEPSPEECH_SCORER = DEEPSPEECH_MODEL_DIRECTORY + 'deepspeech-0.7.0-models.scorer'

# Abstract superclass for different speech-to-text converters
# The following engines are currently supported
# 
# sphinx
# deepspeech
class SpeechParser():
    
    def __init__(self, engine = 'sphinx'):
        self.engine = engine
        self.logger = logging.getLogger(__name__)
        
    def parse(self, wav_file : str) -> str:
        self.logger.debug(f"Parsing voice from {wav_file}")
        if self.engine == 'sphinx':
            return self.parse_sphinx(wav_file)
        elif self.engine == 'deepspeech':
            return self.parse_deepspeech(wav_file)
        else:
            return None

    def parse_sphinx(self, wav_file : str) -> str:
        r = sr.Recognizer()
        with sr.AudioFile(wav_file) as source:
            voice = r.record(source)  # read the entire audio file
        try:
            text = "*I think you said:*\n " + r.recognize_sphinx(voice)
        except sr.UnknownValueError:
            text = "Sorry, I could not understand what you said."
        except sr.RequestError:
            text = "There was an error while trying to recognize what you said"
        return text

    def parse_deepspeech(self, wav_file : str) -> str:
        self.logger.debug(f"Using model {DEEPSPEECH_MODEL} and scorer {DEEPSPEECH_SCORER}")
        self.logger.debug(f"Parsing audio file {wav_file}...")
        result_json = subprocess.check_output(['deepspeech', '--model', DEEPSPEECH_MODEL, '--scorer', DEEPSPEECH_SCORER, '--audio', wav_file, '--json'])
        results = json.loads(result_json)['transcripts'][0]

        words = results['words']#' '.join([words['word'] for words in results['words']])
        return ' '.join([item['word'] for item in words])


    def to_wav(self, voice_file : str) -> str:    
        wav_file = ''.join(voice_file.split('.')[:-1]) + '.wav' # substitute file ending with '.wav'  

        # Convert to wav
        self.logger.info(f"Converting {voice_file} to {wav_file}...")
        subprocess.run(['ffmpeg', '-y', '-i', voice_file, wav_file])
        return wav_file