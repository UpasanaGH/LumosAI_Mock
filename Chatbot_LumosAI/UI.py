css = '''
<style>
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
}
.chat-message.user {
    background-color: #2b313e
}
.chat-message.bot {
    background-color: #475063
}
.chat-message .avatar {
  width: 20%;
}
.chat-message .avatar img {
  max-width: 78px;
  max-height: 78px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 80%;
  padding: 0 1.5rem;
  color: #fff;
}
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://imgcdn.stablediffusionweb.com/2024/4/2/744178fb-5267-4ee0-bba7-e9314c82637e.jpg">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <img src="https://img.freepik.com/free-photo/androgynous-avatar-non-binary-queer-person_23-2151100205.jpg?size=626&ext=jpg&ga=GA1.1.2008272138.1720569600&semt=ais_user">
    </div>    
    <div class="message">{{MSG}}</div>
</div>
'''
