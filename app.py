import streamlit as st
import streamlit.components.v1 as components
import instaloader
import os
import base64
import numpy as np
from PIL import Image
from image_similarity_measures.quality_metrics import rmse

st.set_page_config(
    page_title="Instagram image similarity checker",
    page_icon="favicon.png"
)

bot = instaloader.Instaloader()
bot.login(st.secrets["instaUser"],st.secrets["instaPw"])

st.header('Instagram image similarity checker')

def create_card(profile):
    bot.download_profilepic(profile)
    pp = os.listdir(profile.username)
    with open(f"{profile.username}/{pp[0]}","rb") as f:
        contents = f.read()
        imgb64 = base64.b64encode(contents).decode("utf-8")

    components.html(f"""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" integrity="sha384-xOolHFLEh07PJGoPkLv1IbcEPTNtaed2xpHsD9ESMhqIYd0nLMwNLD69Npy4HI+N" crossorigin="anonymous">
        <script src="https://cdn.jsdelivr.net/npm/jquery@3.5.1/dist/jquery.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.min.js" integrity="sha384-+sLIOodYLS7CIrQpBjl+C7nPvqq+FbNUBDunl/OZv93DB7Ln/533i8e/mZXLi/P+" crossorigin="anonymous"></script>
        <div class="card">
            <div class="row no-gutters">
                <div class="col-4">
                    <img src="data:image/gif;base64,{imgb64}" style="width:100%">
                </div>
                <div class="col-8">
                    <div class="card-body p3">
                        <h5 class="card-title">{profile.username}</h5>
                        <h6 class="card-subtitle mb-4 text-muted">{profile.userid}</h6>
                        <span class="card-text"><strong>{profile.followers}</strong> followers</span><br/>
                        <span class="card-text"><strong>{profile.followees}</strong> following</span><br/>
                        <span class="card-text"><strong>{profile.mediacount}</strong> posts</span><br/>
                    </div>
                </div>
            </div>
        </div>
    """, height=250)

def get_images(profile):
    progbar = st.progress(0.0)
    progtext = st.empty()
    try:
        os.mkdir(f"i{profile.userid}")
    except:
        progbar.progress(1.0)
        progtext.text("Already loaded posts")
        return
    for i,post in enumerate(profile.get_posts()):
        bot.download_pic(f"i{profile.userid}/{post.shortcode}", post.url, post.date) # download
        im = Image.open(f"i{profile.userid}/{post.shortcode}.jpg")
        ds = im.resize((40,40)) # downsample
        ds.save(f"i{profile.userid}/{post.shortcode}.jpg")
        progbar.progress((i+1)/profile.mediacount)
        progtext.text(f"{i+1}/{profile.mediacount} posts loaded")

user = st.text_input("Your instagram profile username")

if user:
    userP = instaloader.Profile.from_username(bot.context, user)
    create_card(userP)
    get_images(userP)

comp = st.text_input("Competitor's instagram profile username")

if comp:
    compP = instaloader.Profile.from_username(bot.context, comp)
    create_card(compP)
    get_images(compP)

# image similarity
if user and comp:
    simbar = st.progress(0.0)
    simtext = st.empty()
    similarity_measures = {}
    for i,u in enumerate(os.listdir(f"i{userP.userid}")):
        for j,c in enumerate(os.listdir(f"i{compP.userid}")):
            unp = np.array(Image.open(f"i{userP.userid}/{u}"))
            cnp = np.array(Image.open(f"i{compP.userid}/{c}"))
            similarity_measures[f"{u}__{c}"] = rmse(unp,cnp)
            simbar.progress((i*compP.mediacount+j+1)/(userP.mediacount*compP.mediacount))
            simtext.text(f"{i*compP.mediacount+j+1}/{userP.mediacount*compP.mediacount} pairs of images compared")

    # similarities above a certain threshold (return urls)
    st.markdown("#### Image pairs with a similarity above threshold")
    with st.spinner("Please wait..."):
        for k,v in similarity_measures.items():
            if v < 0.001:
                p1,p2 = k.split('__')
                p1 = instaloader.Post.from_shortcode(bot.context, p1[:-4])
                p2 = instaloader.Post.from_shortcode(bot.context, p2[:-4])
                st.write(f"[{p1.shortcode}]({p1.url}), [{p2.shortcode}]({p2.url})")

    # most similar
    with st.spinner("Please wait..."):
        p1,p2 = min(similarity_measures, key=similarity_measures.get).split('__')
        p1 = instaloader.Post.from_shortcode(bot.context, p1[:-4])
        p2 = instaloader.Post.from_shortcode(bot.context, p2[:-4])
        st.write(f"#### Most similar image pair: [{p1.shortcode}]({p1.url}), [{p2.shortcode}]({p2.url})")
