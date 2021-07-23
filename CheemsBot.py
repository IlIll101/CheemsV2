from discord.ext import tasks, commands
from yahoo_fin.stock_info import *
from requests_html import HTMLSession
from matplotlib import pyplot as plt
from github import Github
import discord, os, pandas, datetime as DT, json


BotToken = os.environ['DISCORD_TOKEN']
bot = commands.AutoShardedBot(shard_count=10, command_prefix = '!', help_command=None)
bot.launch_time = DT.datetime.utcnow()

@tasks.loop(seconds=10800)
async def leaderboardupdate():
    userdatalist = os.listdir('StockUserData')
    networthvalues = {}
    leaderboardsave = {'TimeOfUpdate' : str((DT.datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S'))}
    for x in userdatalist:
        profile = None
        with open(("StockUserData/" + x), "r") as path:
            profile = json.load(path)
        networthvalues.update({profile['Username'] : profile['LastSavedNetWorth']})

    sortednetworthvalues = dict(sorted(networthvalues.items(), key=lambda item: item[1], reverse=True))
    
    if len(sortednetworthvalues) <= 24:
        for x in sortednetworthvalues:
            leaderboardsave.update({x : sortednetworthvalues.get(x)})
    else:
        for x, y in enumerate(sortednetworthvalues):
            leaderboardsave.update({y : sortednetworthvalues.get(y)})
            if x >= 24:
                break
            

    with open("LeaderBoard", "w") as path:
        json.dump(leaderboardsave, path)
        
@tasks.loop(seconds=1800)
async def backupsaves():
    g = Github("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")
    repo = g.search_repositories("IlIll101/CheemsV2")[0]
    userdatalist = os.listdir('StockUserData/')
    for y in userdatalist:
        profile = None
        x = str(y)
        try:
            contents = repo.get_contents("StockUserData/" + x)
            repo.delete_file(contents.path, "SaveUpdating", contents.sha)
            with open("StockUserData/" +  x, "r") as path:
                profile = json.load(path)
            repo.create_file("StockUserData/" + x, "SaveUpdating", str(profile))
        except:
            with open("StockUserData/" +  x, "r") as path:
                profile = json.load(path)
            repo.create_file("StockUserData/" + x, "SaveUpdating", str(profile))
            
    backupreport = {'FilesBacked' : len(userdatalist),
                    'TimeOfSave' : str((DT.datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S'))}

    with open("BackUpReport", "w") as path:
        json.dump(backupreport, path)

    embed = discord.Embed(title="Backup succsessful!",
                          timestamp=DT.datetime.strptime(backupreport.get('TimeOfSave'), '%Y-%m-%d %H:%M:%S'),
                          color=discord.Color.from_rgb(135, 206, 235))
    embed.add_field(name="Files saved:",
                    value=str(backupreport.get('FilesBacked')),
                    inline=False)

    embed.set_footer(text="Time of backup")
    
    await bot.get_channel(int(os.environ['BACKUP_CHANNEL_ID'])).send(embed=embed)
               
@bot.event
async def on_ready():
    print("Bot is ready!")
    backupsaves.start()
    leaderboardupdate.start()
    await bot.change_presence(activity=discord.Game(name='Prefix is "!"'))
    
@bot.command()
@commands.cooldown(1, 5.0, commands.BucketType.user)
async def uptime(ctx):
    commandauthorid = ctx.message.author.id
    delta_uptime = DT.datetime.utcnow() - bot.launch_time
    hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    embed = discord.Embed(title="Online for " + f"{days}d, {hours}h, {minutes}m",
                          color=discord.Color.from_rgb(135, 206, 235))
    
    await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)

@uptime.error
async def cooldownerror(ctx, error):
    commandauthorid = ctx.message.author.id
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title='Request Denied',
                              description='**There is a cooldown of 5 seconds on this command**',
                              color=discord.Color.red())

        await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)
        
@bot.command()
@commands.cooldown(1, 5.0, commands.BucketType.user)
async def help(ctx):
    commandauthorid = ctx.message.author.id
    embed = discord.Embed(title="Commands", 
                          color=discord.Color.from_rgb(135, 206, 235))
    embed.add_field(name="Stocks",
                    value="**!myprofile** - displays your stock profile/creates a profile\n" +
                    "**!buy <ticker> <amount>** - buys a share of a specific stock\n" +
                    "**!sell <ticker> <amount>** - sells a share of a specific stock that you own\n" +
                    "**!stockprice <ticker>** - displays the price and stats about a stock\n" +
                    "**!stockearnings <ticker>** - displays the earnings of a stock\n" +
                    "**!topgainers** - displays top gainers for the day\n" +
                    "**!toplosers** - displays top losers for the day")
    embed.add_field(name="Misc",
                    value="**!servercount** - displays the server count\n" +
                    "**!leaderboard** - displays the leaderboard (updated every hour)\n" +
                    "**!uptime** - displays the uptime of the bot\n" +
                    "**!backupstatus** - displays info on the last save backup")
    
    await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)
                    
@help.error
async def cooldownerror(ctx, error):
    commandauthorid = ctx.message.author.id
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title='Request Denied',
                              description='**There is a cooldown of 5 seconds on this command**',
                              color=discord.Color.red())

        await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)

@bot.command()
@commands.cooldown(1, 5.0, commands.BucketType.user)
async def servercount(ctx):
    commandauthorid = ctx.message.author.id
    embed = discord.Embed(title=str(len(bot.guilds)) + " servers",
                          color=discord.Color.from_rgb(135, 206, 235))
    
    await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)

@servercount.error
async def cooldownerror(ctx, error):
    commandauthorid = ctx.message.author.id
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title='Request Denied',
                              description='**There is a cooldown of 5 seconds on this command**',
                              color=discord.Color.red())

        await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)
    
@bot.command()
@commands.cooldown(1, 5.0, commands.BucketType.user)
async def backupstatus(ctx):
    commandauthorid = ctx.message.author.id
    backupreport = None
    with open("BackUpReport", "r") as path:
        backupreport = json.load(path)

    embed = discord.Embed(title="Backup info",
                          timestamp=DT.datetime.strptime(backupreport.get('TimeOfSave'), '%Y-%m-%d %H:%M:%S'),
                          color=discord.Color.from_rgb(135, 206, 235))
    embed.add_field(name="Files saved:",
                    value=str(backupreport.get('FilesBacked')),
                    inline=False)
    embed.set_footer(text="Time of backup")
    await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)

@backupstatus.error
async def cooldownerror(ctx, error):
    commandauthorid = ctx.message.author.id
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title='Request Denied',
                              description='**There is a cooldown of 5 seconds on this command**',
                              color=discord.Color.red())

        await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)
        
@bot.command()
@commands.cooldown(1, 5.0, commands.BucketType.user)
async def leaderboard(ctx):
    leaderboarddict = None
    with open("LeaderBoard", "r") as path:
        leaderboarddict = json.load(path)

    leaderboarddesc = ""
    for x, y in enumerate(leaderboarddict):
        if x == 0:
            pass
        else:
            leaderboarddesc = leaderboarddesc + "**" + str(x) + ". " + y + "** : $" + str(leaderboarddict.get(y)) + "\n"
    embed = discord.Embed(title="Top 25 Traders", 
                          description=leaderboarddesc,
                          timestamp=DT.datetime.strptime(leaderboarddict.get('TimeOfUpdate'), '%Y-%m-%d %H:%M:%S'),
                          color=discord.Color.from_rgb(255, 255, 0))
    
    embed.set_footer(text="Last Updated")
        
    await ctx.send(embed=embed)
                    
@leaderboard.error
async def cooldownerror(ctx, error):
    commandauthorid = ctx.message.author.id
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title='Request Denied',
                              description='**There is a cooldown of 5 seconds on this command**',
                              color=discord.Color.red())

        await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)
    
    
@bot.command()
@commands.cooldown(1, 5.0, commands.BucketType.user)
async def stockprice(ctx, stockname):
    try:
        plt.rcParams.update({'font.size': 12})
        fig = plt.figure(figsize=(15, 20))

        datatable = {"Today" : None,
                     "TodayMins" : None,
                     "Week" : get_data(stockname, start_date = DT.date.today() - DT.timedelta(days=7), end_date = DT.date.today(), index_as_date = False),
                     "Month": get_data(stockname, start_date = DT.date.today() - DT.timedelta(days=22), end_date = DT.date.today(), index_as_date = False),
                     "Year" : get_data(stockname, start_date = DT.date.today() - DT.timedelta(days=356), end_date = DT.date.today(), index_as_date = False),
                     "All" : get_data(stockname, index_as_date = False)}


        stockinfo = get_quote_data(stockname)
        stocktable = get_quote_table(stockname)

        #Doesn't Work anymore for some reason :/
        #if True == :
            #datatable['TodayMins'] = get_data(stockname, start_date = DT.date.today() - DT.timedelta(days=1), index_as_date = False, interval = "1m")
            #plt.subplot(5, 1, 1) #Week Graph
            #plt.plot(datatable.get("TodayMins")['date'], datatable.get("TodayMins")['open'], color='g')
            #plt.title('Today')
            #plt.grid(True)

        plt.subplot(5, 1, 2) #Week Graph
        plt.plot(datatable.get("Week")['date'], datatable.get("Week")['open'], color='c')
        plt.title('Week')
        plt.grid(True)

        plt.subplot(5, 1, 3) #Month Graph
        plt.plot(datatable.get("Month")['date'], datatable.get("Month")['open'], color='b')
        plt.title('Month')
        plt.grid(True)

        plt.subplot(5, 1, 4) #Year Graph
        plt.plot(datatable.get("Year")['date'], datatable.get("Year")['open'], color='y')
        plt.title('Year')
        plt.grid(True)

        plt.subplot(5, 1, 5) #All Graph
        plt.plot(datatable.get("All")['date'], datatable.get("All")['open'], color='r')
        plt.title('All Time')
        plt.grid(True)

        fig.tight_layout()
        fig.savefig('graph.png', bbox_inches='tight', dpi=80) #Saves plot as image

        imagefile = discord.File("graph.png", filename="graph.png")

        if stockinfo.get("regularMarketChange") < 0:
            embed = discord.Embed(title=(stockinfo.get('longName') + ' (' + stockname.upper() + ')'),
                              description="**" + str(round(get_live_price(stockname.upper()), 2)) + '**  :arrow_down_small: ' + str(round(stockinfo.get("regularMarketChange"), 2)) + " (" + str(round(stockinfo.get("regularMarketChangePercent"), 2)) + "%)\n" + stockinfo.get("fullExchangeName"))
                                  
        elif stockinfo.get("regularMarketChange") > 0:
            embed = discord.Embed(title=(stockinfo.get('longName') + ' (' + stockname.upper() + ')'),
                              description="**" + str(round(get_live_price(stockname.upper()), 2)) + '**  :arrow_up_small: ' + str(round(stockinfo.get("regularMarketChange"), 2)) + " (" + str(round(stockinfo.get("regularMarketChangePercent"), 2)) + "%)\n" + stockinfo.get("fullExchangeName"))
        elif stockinfo.get("regularMarketChange") == 0:
            embed = discord.Embed(title=(stockinfo.get('longName') + ' (' + stockname.upper() + ')'),
                              description="**" + str(round(get_live_price(stockname.upper()), 2)) + '**  :pause_button: ' + str(round(stockinfo.get("regularMarketChange"), 2)) + " (" + str(round(stockinfo.get("regularMarketChangePercent"), 2)) + "%)\n" + stockinfo.get("fullExchangeName"))
    
        embed.add_field(name="Market Status",
                        value=get_market_status(),
                        inline=False)
        embed.add_field(name="Open",
                        value=round(stocktable.get("Open"), 2))
        embed.add_field(name="High",
                        value=round(stockinfo.get("regularMarketDayHigh"), 2))
        embed.add_field(name="Low",
                        value=round(stockinfo.get("regularMarketDayLow"), 2))
        embed.add_field(name="Previous Close",
                        value=round(stockinfo.get("regularMarketPreviousClose"), 2))
        embed.add_field(name="52wk High",
                        value=round(stockinfo.get("fiftyTwoWeekHigh"), 2))
        embed.add_field(name="52wk Low",
                        value=round(stockinfo.get("fiftyTwoWeekLow"), 2))
        embed.add_field(name="Volume",
                        value=round(stockinfo.get("regularMarketVolume"), 2))
        embed.add_field(name="PE Ratio",
                        value=round(stocktable.get("PE Ratio (TTM)"), 2))
        embed.add_field(name="EPS",
                        value=round(stocktable.get("EPS (TTM)"), 2))
        
        embed.set_image(url="attachment://graph.png")

    

        await ctx.send(file=imagefile, embed=embed)

    except Exception as exc:
        print(exc)
        await ctx.send("Please use a valid stock ticker!")

@stockprice.error
async def cooldownerror(ctx, error):
    commandauthorid = ctx.message.author.id
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title='Request Denied',
                              description='**There is a cooldown of 5 seconds on this command**',
                              color=discord.Color.red())

        await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)

@bot.command()
@commands.cooldown(1, 5.0, commands.BucketType.user)
async def stockearnings(ctx, stockname):
    stockinfo = get_quote_data(stockname)
    stockearnings = get_earnings(stockname)
    earningslist = ""
    for i in stockearnings:
        if i == 'quarterly_results':
            pass
        else:
            earningslist = earningslist + "**" + i + "**\n"
            for x in stockearnings.get(i).index:
                earningslist = earningslist + "**" + str(stockearnings.get(i).iloc[x]["date"]) + ",** "
                earningslist = earningslist + " **Revenue :** " + str(stockearnings.get(i).iloc[x]["revenue"]) + ", "
                earningslist = earningslist + " **Earnings :** " + str(stockearnings.get(i).iloc[x]["earnings"]) + "\n"

            earningslist = earningslist + "\n"

    embed = discord.Embed(title=(stockinfo.get('longName') + ' (' + stockname.upper() + ')'),
                          description= "**Currency : **" + stockinfo.get("currency"))
    embed.add_field(name="Earnings",
                        value=earningslist)
    await ctx.send(embed=embed)
    
@stockearnings.error
async def cooldownerror(ctx, error):
    commandauthorid = ctx.message.author.id
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title='Request Denied',
                              description='**There is a cooldown of 5 seconds on this command**',
                              color=discord.Color.red())

        await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)    
    
@bot.command()
@commands.cooldown(1, 5.0, commands.BucketType.user)
async def topgainers(ctx):
    gaindata = get_day_gainers()
    gainlist = ""
    for i in (gaindata.index):
        gainlist = gainlist + "**" + gaindata.iloc[i]["Symbol"] + "**   " + str(round(gaindata.iloc[i]["Price (Intraday)"], 2)) + "    "
        if gaindata.iloc[i]["Change"] > 0:
            gainlist = gainlist + ":arrow_up_small: " + str(round(gaindata.iloc[i]["Change"], 2)) + " (" + str(round(gaindata.iloc[i]["% Change"], 2)) + "%)\n"
        elif gaindata.iloc[i]["Change"] < 0:
            gainlist = gainlist + ":arrow_down_small: " + str(round(gaindata.iloc[i]["Change"], 2)) + " (" + str(round(gaindata.iloc[i]["% Change"], 2)) + "%)\n"
        elif gaindata.iloc[i]["Change"] == 0:
            gainlist = gainlist + ":pause_button: " + str(round(gaindata.iloc[i]["Change"], 2)) + " (" + str(round(gaindata.iloc[i]["% Change"], 2)) + "%)\n"
        if i >= 49:
            break
            
    embed = discord.Embed(title="Top 50 Day Gainers",
                              description=gainlist)

    await ctx.send(embed=embed)

@topgainers.error
async def cooldownerror(ctx, error):
    commandauthorid = ctx.message.author.id
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title='Request Denied',
                              description='**There is a cooldown of 5 seconds on this command**',
                              color=discord.Color.red())

        await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)
        
@bot.command()
@commands.cooldown(1, 5.0, commands.BucketType.user)
async def toplosers(ctx):
    lossdata = get_day_losers()
    losslist = ""
    for i in (lossdata.index):
        losslist = losslist + "**" + lossdata.iloc[i]["Symbol"] + "**   " + str(round(lossdata.iloc[i]["Price (Intraday)"], 2)) + "    "
        if lossdata.iloc[i]["Change"] > 0:
            losslist = losslist + ":arrow_up_small: " + str(round(lossdata.iloc[i]["Change"], 2)) + " (" + str(round(lossdata.iloc[i]["% Change"], 2)) + "%)\n"
        elif lossdata.iloc[i]["Change"] < 0:
            losslist = losslist + ":arrow_down_small: " + str(round(lossdata.iloc[i]["Change"], 2)) + " (" + str(round(lossdata.iloc[i]["% Change"], 2)) + "%)\n"
        elif lossdata.iloc[i]["Change"] == 0:
            losslist = losslist + ":pause_button: " + str(round(lossdata.iloc[i]["Change"], 2)) + " (" + str(round(lossdata.iloc[i]["% Change"], 2)) + "%)\n"
        if i >= 49:
            break
            
    embed = discord.Embed(title="Top 50 Day Losers",
                              description=losslist)

    await ctx.send(embed=embed)

@toplosers.error
async def cooldownerror(ctx, error):
    commandauthorid = ctx.message.author.id
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title='Request Denied',
                              description='**There is a cooldown of 5 seconds on this command**',
                              color=discord.Color.red())

        await ctx.send('<@' + str(commandauthorid) + '>', embed=embed) 

@bot.command()
@commands.cooldown(1, 5.0, commands.BucketType.user)
async def myprofile(ctx):
    commandauthorid = ctx.message.author.id
    profile = None
    try:
        with open("StockUserData/" + str(commandauthorid), "r") as path:
            profile = json.load(path)
            
        embed = discord.Embed(title=str(ctx.author) + "'s profile:")
        embed.set_thumbnail(url=(ctx.message.author.avatar_url))

        networthvalue = profile['Capital']
        for x in profile['Shares Owned']:
            if profile['Shares Owned'] == 'None':
                break
            
            stockprice = round(get_live_price(x.upper()), 2)
            networthvalue = networthvalue + (stockprice * profile['Shares Owned'][x][0])

        profile['LastSavedNetWorth'] = networthvalue
        profile['Username'] = str(ctx.author)
        embed.add_field(name='Net Worth',
                        value=round(networthvalue, 2),
                        inline=False)
        
        for x in profile:
            if x == 'Shares Owned':
                if profile[x] == 'None':
                    embed.add_field(name=x,
                                    value=profile[x],
                                    inline=False)

                else:
                    ownedstocks = ""
                    for i in profile[x]:
                        ownedstocks = ownedstocks + "**" + str(i) + " : **" + str(profile[x][i][0]) + " : "
                        #for the code down below I didnt want the strring adding stuff to take up a big line.
                        if profile[x][i][0] * get_live_price(i.upper()) - profile[x][i][1] > 0:
                            ownedstocks = (ownedstocks +" :arrow_up_small: " +
                                           str(round(profile[x][i][0] * get_live_price(i.upper()) - profile[x][i][1], 2)) + 
                                           " (" + str(round((profile[x][i][0] * get_live_price(i.upper()) - profile[x][i][1])/(profile[x][i][1]) * 100, 2)) + "%)\n")
                                           
                        elif profile[x][i][0] * get_live_price(i.upper()) - profile[x][i][1] < 0:
                            ownedstocks = (ownedstocks +" :arrow_down_small: " +
                                           str(round(profile[x][i][0] * get_live_price(i.upper()) - profile[x][i][1], 2)) + 
                                           " (" + str(round((profile[x][i][0] * get_live_price(i.upper()) - profile[x][i][1])/(profile[x][i][1]) * 100, 2)) + "%)\n")
                            
                        elif profile[x][i][0] * get_live_price(i.upper()) - profile[x][i][1] == 0:
                            ownedstocks = (ownedstocks +" :pause_button: " +
                                           str(round(profile[x][i][0] * get_live_price(i.upper()) - profile[x][i][1], 2)) + 
                                           " (" + str(round((profile[x][i][0] * get_live_price(i.upper()) - profile[x][i][1])/(profile[x][i][1]) * 100, 2)) + "%)\n")
                                           
                            
                    embed.add_field(name=x,
                                value=ownedstocks,
                                inline=False)

            elif x == 'Capital':
                embed.add_field(name=x,
                                value=round(profile[x], 2),
                                inline=False)
                
            elif x == 'Username' or x == 'LastSavedNetWorth':
                pass

            else:
                embed.add_field(name=x,
                                value=profile[x],
                                inline=False)

        with open("StockUserData/" + str(commandauthorid), "w") as path:
            json.dump(profile, path)
            
        await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)
        
    except:
        NewUserData = {'Username' : str(ctx.author),
                       'LastSavedNetWorth' : 2000,
                       'Capital' : 2000,
                       'Shares Owned' : 'None'}
        with open("StockUserData/" + str(commandauthorid), "w") as path:
            json.dump(NewUserData, path)

        await ctx.send('<@' + str(commandauthorid) + '> ' + "You did not previously have a profile in the database, so a new profile for you has been created!")

@myprofile.error
async def cooldownerror(ctx, error):
    commandauthorid = ctx.message.author.id
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title='Request Denied',
                              description='**There is a cooldown of 5 seconds on this command**',
                              color=discord.Color.red())

        await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)
        
@bot.command()
@commands.cooldown(1, 5.0, commands.BucketType.user)
async def buy(ctx, stockname, amount):
    quant = int(amount)
    commandauthorid = ctx.message.author.id
    profile = None
    try:
        with open("StockUserData/" + str(commandauthorid), "r") as path:
            profile = json.load(path)
            
        stockprice = get_live_price(stockname)
        
        if len(profile['Shares Owned']) <= 4:
            if quant > 0 and stockprice * quant <= profile['Capital']:
                if profile['Shares Owned'] == 'None':
                    profile['Shares Owned'] = {stockname.upper() : [quant, round(quant * stockprice, 2)]}
                    profile['Capital'] = profile['Capital'] - round(quant * stockprice, 2)
                elif str(stockname.upper()) in profile['Shares Owned']:
                    profile['Shares Owned'][stockname.upper()] = [profile['Shares Owned'][stockname.upper()][0] + quant, profile['Shares Owned'][stockname.upper()][1] + round(quant * stockprice, 2)]
                    profile['Capital'] = profile['Capital'] - round(quant * stockprice, 2)
                else:
                    profile['Shares Owned'][stockname.upper()] = [quant, round(quant * stockprice, 2)]
                    profile['Capital'] = profile['Capital'] - round(quant * stockprice, 2)

                with open("StockUserData/" + str(commandauthorid), "w") as path:
                    json.dump(profile, path)
                    
                embed = discord.Embed(title='Transaction Sucsessful',
                                      description='**You bought ' + amount + ' shares of ' + stockname.upper() + ' for ' + str(round(quant * stockprice, 2)) + "**",
                                      color=discord.Color.green())
                await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)
                

            else:
                embed = discord.Embed(title='Transaction Denied',
                                      description='**Please input a valid amount of shares**',
                                      color=discord.Color.red())
                await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)
        else:
            embed = discord.Embed(title='Transaction Denied',
                                  description='**You are at the limit of shares. Due to limitations, you can only own 5 different shares at a time.**',
                                  color=discord.Color.red())
            await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)
            
            
            

    except:
         embed = discord.Embed(title='Transaction Denied',
                                  description='**Please input a valid stock ticker, or create a profile if you do not have one already using the myprofile**',
                                  color=discord.Color.red())
         await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)

@buy.error
async def cooldownerror(ctx, error):
    commandauthorid = ctx.message.author.id
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title='Request Denied',
                              description='**There is a cooldown of 5 seconds on this command**',
                              color=discord.Color.red())

        await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)
        
@bot.command()
@commands.cooldown(1, 5.0, commands.BucketType.user)
async def sell(ctx, stockname, amount):
    quant = int(amount)
    commandauthorid = ctx.message.author.id
    profile = None
    try:
        with open("StockUserData/" + str(commandauthorid), "r") as path:
            profile = json.load(path)
            
        stockprice = get_live_price(stockname)
        if quant > 0 and stockprice * quant <= profile['Capital']:
            if str(stockname.upper()) in profile['Shares Owned'] and quant <= profile['Shares Owned'][stockname.upper()][0]:
                if quant < profile['Shares Owned'][stockname.upper()][0]:
                    profile['Shares Owned'][stockname.upper()] = [profile['Shares Owned'][stockname.upper()][0] - quant, profile['Shares Owned'][stockname.upper()][1] + round(quant * stockprice, 2)]
                    profile['Capital'] = profile['Capital'] + round(quant * stockprice, 2)
                    
                else:
                    del profile['Shares Owned'][stockname.upper()]
                    profile['Capital'] = profile['Capital'] + round(quant * stockprice, 2)
                    if profile['Shares Owned'] == {}:
                        profile['Shares Owned'] = 'None'
            else:
                embed = discord.Embed(title='Transaction Denied',
                                      description='**Please input a valid stock that you own**',
                                      color=discord.Color.red())
                await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)
                return
                    
            with open("StockUserData/" + str(commandauthorid), "w") as path:
                json.dump(profile, path)
                
            embed = discord.Embed(title='Transaction Sucsessful',
                                  description='**You sold ' + amount + ' shares of ' + stockname.upper() + ' and earned ' + str(round(quant * stockprice, 2)) + "**",
                                  color=discord.Color.green())
            await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)

        else:
            embed = discord.Embed(title='Transaction Denied',
                                  description='**Please input a valid amount of shares**',
                                  color=discord.Color.red())
            await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)

    except:
         embed = discord.Embed(title='Transaction Denied',
                                  description='**Please input a valid stock ticker, or create a profile if you do not have one already using the myprofile**',
                                  color=discord.Color.red())
         await ctx.send('<@' + str(commandauthorid) + '>', embed=embed)

@sell.error
async def cooldownerror(ctx, error):
    commandauthorid = ctx.message.author.id
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title='Request Denied',
                              description='**There is a cooldown of 5 seconds on this command**',
                              color=discord.Color.red())

        await ctx.send('<@' + str(commandauthorid) + '>', embed=embed) 
                
            
bot.run(BotToken)           
        
        

        



