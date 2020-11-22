import discord
import asyncio
import os
import datetime
from pytz import timezone, utc
from discord.ext import commands
import sqlite3
import random


def calc_d_day(doom):
    KST = datetime.timezone(datetime.timedelta(hours=9))
    utc_now = datetime.datetime.utcnow()
    kr_now = utc.localize(utc_now).astimezone(KST)

    delta = doom - kr_now    

    if delta.days < 0:
        d_days = -1 - delta.days
        d_hour = (86400 - delta.seconds) // 3600
        d_minutes = ((86400 - delta.seconds) // 60) % 60
        d_seconds = (86400 - delta.seconds) % 60
        return [False, d_days, d_hour, d_minutes, d_seconds]
    else:
        d_days = delta.days
        d_hour = delta.seconds // 3600
        d_minutes = (delta.seconds // 60) % 60
        d_seconds = delta.seconds % 60
        return [True, d_days, d_hour, d_minutes, d_seconds]

def adapt_datetime(dt):
    ts = dt.strftime('%c')
    tz = dt.strftime('%z')
    if len(tz) == 0:
        tz = '+0000'
    return '{} {}'.format(ts, tz)

def convert_datetime(dt):
    return datetime.datetime.strptime(dt.decode(), '%c %z')

if __name__ == "__main__":

    sqlite3.register_adapter(datetime.datetime, adapt_datetime)
    sqlite3.register_converter('datetime', convert_datetime)
    
    conn = sqlite3.connect("secretary.db", detect_types = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

    cur = conn.cursor()

    create_table_query = '''
                         CREATE TABLE IF NOT EXISTS Dday (
                            id INTEGER AUTO_INCREMENT PRIMARY KEY,
                            guild TEXT NOT NULL,
                            name TEXT NOT NULL,
                            date datetime
                         );
                         '''
    cur.execute(create_table_query)
    conn.commit()

    create_table_query = '''
                         CREATE TABLE IF NOT EXISTS Weight (
                            id INTEGER AUTO_INCREMENT PRIMARY KEY,
                            guild TEXT NOT NULL,
                            name TEXT NOT NULL,
                            timez datetime,
                            weight REAL
                         );
                         '''
    cur.execute(create_table_query)
    conn.commit()
    
    t = open('token.txt', 'r')
    token = t.read().rstrip()
    blank = '\u200B'

    client = discord.Client()

    @client.event
    async def on_ready():
        print('start')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('!'):
            query = message.content[1:]
            query_words = query.split()
            if len(query_words) == 1:
                find_date_query = 'SELECT date from Dday where guild = ? and name = ?'
                cur.execute(find_date_query, (message.guild.id, query))
                result = cur.fetchall()
                for row in result:
                    delta = calc_d_day(row[0])
                    if delta[0]:
                        await message.channel.send('{}일 {}시간 {}분 {}초 남았습니다.'.format(delta[1], delta[2], delta[3], delta[4]))
                    else:
                        await message.channel.send('{}일 {}시간 {}분 {}초 지났습니다.'.format(delta[1], delta[2], delta[3], delta[4]))

        if message.content.startswith('!디데이'):
            query = message.content[4:]
            query_words = query.split()

            if len(query_words) == 0:
                return
            elif len(query_words) == 1:
                d_name = query_words[0]
                find_date_query = 'SELECT date from Dday where guild = ? and name = ?'
                cur.execute(find_date_query, (message.guild.id, query))
                result = cur.fetchall()
                if len(result) > 0:
                    for row in result:
                        delta = calc_d_day(row[0])
                        if delta[0]:
                            await message.channel.send('{}일 {}시간 {}분 {}초 남았습니다.'.format(delta[1], delta[2], delta[3], delta[4]))
                        else:
                            await message.channel.send('{}일 {}시간 {}분 {}초 지났습니다.'.format(delta[1], delta[2], delta[3], delta[4]))
                else:
                    await message.channel.send('{} 디데이가 아직 등록되지 않았습니다.'.format(d_name))
                    await message.channel.send('!디데이 추가 (이름) (YYYY-MM-DD) ?(HH:MM:SS) 로 등록해주세요.')
                
            else:
                if query_words[0] == '추가':
                    d_name = query_words[1]
                    d_date = query_words[2].split('-')
                    d_time = [23, 59, 59] if len(query_words) <= 3 else query_words[3].split(':')

                    KST = datetime.timezone(datetime.timedelta(hours=9))
                    d_datetime = datetime.datetime(int(d_date[0]), int(d_date[1]), int(d_date[2]), int(d_time[0]), int(d_time[1]), int(d_time[2]), tzinfo=KST)

                    insert_date_query = 'insert into Dday(guild, name, date) VALUES (?, ?, ?)'
                    cur.execute(insert_date_query, (message.guild.id, d_name, d_datetime))
                    conn.commit()

                    delta = calc_d_day(d_datetime)
                    if delta[0]:
                        await message.channel.send('{}일 {}시간 {}분 {}초 남은 {} 디데이가 등록되었습니다.'.format(delta[1], delta[2], delta[3], delta[4], d_name))
                    else:
                        await message.channel.send('{}일 {}시간 {}분 {}초 지난 {} 디데이가 등록되었습니다.'.format(delta[1], delta[2], delta[3], delta[4], d_name))

                elif query_words[0] == '삭제':
                    d_name = query_words[1]

                    find_date_query = 'SELECT date from Dday where guild = ? and name = ?'
                    cur.execute(find_date_query, (message.guild.id, d_name))
                    result = cur.fetchall()

                    if len(result) > 0:
                        delete_date_query = 'delete from Dday where guild = ? and name = ?'
                        cur.execute(delete_date_query, (message.guild.id, d_name))
                        result = cur.fetchall()
                        conn.commit()
                        await message.channel.send('{} 디데이가 삭제되었습니다.'.format(d_name))
                    else:
                        await message.channel.send('{} 디데이가 아직 등록되지 않았습니다.'.format(d_name))
                        await message.channel.send('!디데이 추가 (이름) (YYYY-MM-DD) ?(HH:MM:SS) 로 등록해주세요.')


        if message.content.startswith('!몸무게'):
            query = message.content[5:]
            guild = message.guild.id
            name = str(message.author)

            if query == '출력':
                find_date_query = 'SELECT timez, weight from Weight where guild = ? and name = ?'
                cur.execute(find_date_query, (guild, name))
                result = cur.fetchall()
                result.sort(key = lambda x: x[0])
                await message.channel.send('{}의 몸무게 기록'.format(message.author.name))
                resultString = '```\n'
                for row in result:
                    # await message.channel.send('{}\t{}'.format(row[0].strftime('%Y-%m-%d %H:%M:%S'), row[1]))
                    resultString += '{}\t{}\n'.format(row[0].strftime('%Y-%m-%d %H:%M:%S'), row[1])
                resultString += '```'
                await message.channel.send(resultString)

            else:
                weight = float(query)
                if weight > 0:
                    insert_date_query = 'insert into Weight(guild, name, timez, weight) VALUES (?, ?, ?, ?)'
                    
                    KST = datetime.timezone(datetime.timedelta(hours=9))
                    utc_now = datetime.datetime.utcnow()
                    kr_now = utc.localize(utc_now).astimezone(KST)
                    
                    cur.execute(insert_date_query, (guild, name, kr_now, weight))
                    conn.commit()
                    await message.channel.send('{}의 몸무게 {}가 기록되었습니다.'.format(message.author.name, weight))

        if message.content.startswith('!랜덤'):
            query = message.content[4:]
            ranges = query.split(' ')
            res = random.randint(int(ranges[0]), int(ranges[1]))
            await message.channel.send(res)
        
        if message.content.startswith('!선택'):
            query = message.content[4:]
            candi = query.split(' ')
            if len(candi) > 0:
                res = candi[random.randint(0, len(candi) - 1)]
                await message.channel.send(res)
        
        if message.content.startswith('!help') or message.content.startswith('!도움'):
            embed = discord.Embed(title = "Seretary Bot")
            embed.add_field(name = '!디데이 추가 ... YYYY-MM-DD (HH:MM:SS)', value = "디데이 추가", inline = False)
            embed.add_field(name = '!디데이 삭제 ...', value = "디데이 삭제", inline = False)
            embed.add_field(name = '!디데이 ... or !...', value = "디데이 확인", inline = False)
            embed.add_field(name = '!몸무게 ...', value = "몸무게 기록", inline = False)
            embed.add_field(name = '!몸무게 출력', value = "몸무게 기록 출력", inline = False)
            embed.add_field(name = '!랜덤 a b', value = "a, b 사이 정수 랜덤(inclusive)", inline = False)
            embed.add_field(name = '!선택 a b c d ...', value = "a b c d ... 중 하나 선택", inline = False)
            await message.channel.send(embed = embed)
                
    client.run(token)
