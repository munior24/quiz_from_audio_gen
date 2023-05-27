import whisper
import openai
import streamlit as st
import sounddevice as sd
import soundfile as sf
import time 
import tempfile
import re
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json
import webbrowser

openai.organization = "org-m8Slk26M4czyPKoVdX7E7J0L"
API_KEY= "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"
openai.api_key = API_KEY



model = whisper.load_model("base")
def transcribe_aud(audio_name):
    result = model.transcribe(audio_name)
    print(result["text"])
    return result["text"]


def get_quiz(prompt):
    st.write('Generating the quiz')
    Req = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
        {"role": "user", "content": prompt}
                ]
        )
    quiz_text = Req.choices[0].message.content

    return quiz_text


def record(timer):
    fs = 44100  # Sample rate
    seconds = timer # Duration of recording

    # Start recording
    recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
    st.write('Recording!')
    sd.wait()  # Wait until recording is finished
    st.write("Recording finished!")

    with open('audio.wav', 'wb') as f:
        sf.write(f.name, recording, fs)


def parse_result(quiz):
    quest = re.compile(r'^\d+(?:\)|\.|\-)(.+\?$)')
    opt = re.compile(r'^[a-zA-Z](?:\)|\.|\-)(.+$)')
    ans= re.compile(r'Answer:\s[a-zA-Z](?:\)|\.|\-)(.+$)')
    questions = []
    options=[]          
    sub =[]
    answers =[]
    for line in quiz.splitlines():
        if line == '':
            if sub:
                options.append(sub)
                sub=[]
        else:
            if quest.match(line):
                line_mod = line.strip()
                questions.append(line_mod)
            if opt.match(line):
                line_mod = line.strip()
                sub.append(line_mod)
            if ans.match(line):
                line_mod= line.strip()
                answers.append(line_mod)
    if sub:
        options.append(sub)
    return questions, options
       
def generate_quiz(questions, options):
    SCOPES = "https://www.googleapis.com/auth/forms.body"
    DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

    store = file.Storage('token.json')
    creds = None
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
        creds = tools.run_flow(flow, store)

    form_service = discovery.build('forms', 'v1', http=creds.authorize(
        Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)

    # Request body for creating a form
    NEW_FORM = {
        "info": {
            "title": "Quiz ",
        }
    }
    # Creates the initial form
    result = form_service.forms().create(body=NEW_FORM).execute()
    # Request body to add a multiple-choice question
    # JSON to convert the form into a quiz
    update = {
    "requests": [
        {
            "updateSettings": {
                "settings": {
                    "quizSettings": {
                        "isQuiz": True
                    }
                },
                "updateMask": "quizSettings.isQuiz"
            }
        }
    ]
    }
    # Converts the form into a quiz
    question_setting = form_service.forms().batchUpdate(formId=result["formId"],body=update).execute()
    for i in range(len(questions)): 
        NEW_QUESTION = {
            "requests": [{
                "createItem": {
                    "item": {
                        "title": questions[i],
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [{"value":j} for j in options[i]],
                                    "shuffle": True
                                }
                            }
                        },
                    },
                    "location": {
                        "index": i
                    }
                }
            }]
        }
        question_setting = form_service.forms().batchUpdate(formId=result["formId"], body=NEW_QUESTION).execute()

    get_result = form_service.forms().get(formId=result["formId"]).execute()

    return get_result['responderUri']


if __name__ == "__main__":
        
    st.title("Quiz Generator")
    # st.write("Click the button below to start.")
    option = option = st.sidebar.selectbox("Select a Type Of  Prompt", ("Audio Prompt", "Text Prompt"))
    col1, col2, col3 = st.columns(3)
    if option == "Audio Prompt":
        with col1:
            timer = st.radio("Select duration in seconds:", (5, 10, 20))
        with col2:
            st.write('')
            if st.button('Start Recording'):
                record(timer)
                st.write('')
        with col3:
            st.write('')
            if st.button('Generate Quiz'):
                st.write('transcribing the audio!')
                prompt = transcribe_aud('audio.wav')
                prompt = prompt + '\nThe quiz should have 4 questions each question have 4 options and give the answer for each question.'
                quiz = get_quiz(prompt)
                questions, options = parse_result(quiz)
                url = generate_quiz(questions, options)
                st.write(f'forms URL : {url}')


    if option == "Text Prompt":
            with col1:
                prompt = st.text_input("Write the topic of your Quiz")
                prompt = "Generate a quiz about " + prompt +  '\nThe quiz should have 4 questions each question have 4 options and give the answer for each question.'
            with col2:
                st.write('')
                st.write('')
                if st.button('Generate Quiz'):
                    quiz = get_quiz(prompt)
                    questions, options = parse_result(quiz)
                    url = generate_quiz(questions, options)
                    st.write(f'forms URL : {url}')

        
            
        
        

            



        