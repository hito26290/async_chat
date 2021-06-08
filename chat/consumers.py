import json
from channels.generic.websocket import AsyncWebsocketConsumer
#from asgiref.sync import async_to_sync
import datetime

class ChatConsumer( AsyncWebsocketConsumer ):

    rooms = None

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs )
        if ChatConsumer.rooms is None:
            ChatConsumer.rooms = {} # 空の連想配列
        self.groupName = ''
        self.userName = ''

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        await self.leave_chat()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        if ('join' == text_data_json.get('data_type')):
            self.groupName = text_data_json['roomname']
            self.userName = text_data_json['username']

            await self.channel_layer.group_add( self.groupName, self.channel_name )

            if (ChatConsumer.rooms.get(self.groupName) == None):
                ChatConsumer.rooms[self.groupName] = {'room_name': self.groupName, 'member_list': []}

            ChatConsumer.rooms[self.groupName]['member_list'].append(self.userName)
            await self.member_send()

            await self.announce_send('join')

        elif('message' == text_data_json.get('data_type')):
            message = text_data_json['message']
            image = text_data_json['image']
            data = {
                'type': 'chat_message',
                'message': message,
                'image' : image,
                'username': self.userName,
                'datetime': datetime.datetime.now().strftime( '%Y/%m/%d %H:%M:%S' ),
            }
            await self.channel_layer.group_send( self.groupName, data )


    async def member_send(self):
        memberList = {
            'type': 'member_list', 'members': ChatConsumer.rooms[self.groupName]['member_list']
        }
        await self.channel_layer.group_send( self.groupName,  memberList)

    async def member_list(self, event):
        data_json = {
            'data_type': 'member',
            'members': event['members']
        }
        await self.send(text_data=json.dumps(data_json))

    async def announce_send(self, state):
        if (state == 'join'):
            announce = '"' + self.userName +'"が入室しました'
        elif (state == 'leave'):
            announce = '"' + self.userName +'"が退室しました'
        data = {
            'type': 'chat_message',
            'message': announce,
            'image': '',
            'username': '*システム*',
            'datetime': datetime.datetime.now().strftime( '%Y/%m/%d %H:%M:%S' ),
        }
        await self.channel_layer.group_send( self.groupName, data )


    async def chat_message(self, event):
        data_json = {
            'data_type': 'message',
            'message': event['message'],
            'image': event['image'],
            'username': event['username'],
            'datetime': event['datetime'],
        }

        await self.send( text_data=json.dumps( data_json ) )
        
        



    async def leave_chat(self):
        ChatConsumer.rooms[self.groupName]['member_list'].remove(self.userName)
        await self.member_send()

        if( len(ChatConsumer.rooms[self.groupName]['member_list']) == 0):
            del ChatConsumer.rooms[self.groupName]
        
        await self.announce_send('leave')

        await self.channel_layer.group_discard( self.groupName, self.channel_name )

