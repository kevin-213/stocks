#-*- encoding:utf-8 -*-

import baostock as bs
import pandas as pd
import os
import datetime
from matplotlib import pyplot as plt
import matplotlib
import tkinter
from tkinter import messagebox

g_codes={}

def list_stocks():
    bs.login()
    global g_codes
    rs = bs.query_stock_industry()
    industry_list = []
    while (rs.error_code=='0') & rs.next():
        industry_list.append(rs.get_row_data())
    df_codes = pd.DataFrame(industry_list, columns=rs.fields)
    df_codes.to_csv('./codes.csv', encoding='utf-8', index=False)
    bs.logout()
    return df_codes

def get_stock_today():
    global g_codes
    if os.path.exists('./codes.csv'):
        df_codes = pd.read_csv('./codes.csv')
    else:
        df_codes = list_stocks()
    g_codes = {df_codes.loc[index]['code']:df_codes.loc[index]['code_name'] for index in df_codes.index}
    print('len(g_codes)=%d'%len(g_codes))
    if os.path.exists('./today.csv'):
        df_today = pd.read_csv('./today.csv')
    else:
        if os.path.exists('./all.csv'):
            df_all = pd.read_csv('./all.csv')
        else:
            bs.login()
            dfs = {}
            for code in df_codes['code']:
                fname = 'datas/%s.csv' % code
                if os.path.exists(fname):
                    dfs[code] = pd.read_csv(fname)
                else:
                    print('getting data for stock %s' % code)
                    rs = bs.query_history_k_data_plus(code, 'date,code,open,high,low,close,preclose,volume,amount', start_date='2006-01-01',frequency='d',adjustflag='2')
                    data_list = []
                    while (rs.error_code=='0') & rs.next():
                        data_list.append(rs.get_row_data())
                    dfs[code] = pd.DataFrame(data_list, columns=rs.fields)
                    dfs[code].to_csv(fname, encoding='utf-8', index=False)
            bs.logout() 
            df_all = pd.concat(dfs.values())
            df_all.to_csv('./all.csv', encoding='utf-8', index=False)

        df_all['volume'].apply(float)
        df1 = df_all[df_all['volume'] > 0]
        df2 = df1.groupby('code').aggregate({'date':max, 'high':max, 'low':min})
        df2 = df2.reset_index()
        df3 = df_all[['code', 'date', 'close']]
        df4 = pd.merge(df2, df3, on=['code', 'date'])
        df5 = df4[df4['date'] >= (datetime.date.today()-datetime.timedelta(days=30)).strftime('%4Y-%2m-%2d')]
        df5.rename(columns={'high':'highest', 'low':'lowest'}, inplace=True)
        df_today=df5
        df_today.to_csv('./today.csv',encoding='utf-8',index=False)
    return df_today
             
  
def show_figure(df):
    df['x'] = df.apply(lambda row:row['close']/row['highest'], axis=1)
    df['y'] = df.apply(lambda row:0 if row['lowest']<0 else row['lowest']/row['close'], axis=1)
    x = df['x'].tolist()
    y = df['y'].tolist()
    codes = df['code'].tolist()
    fig = plt.figure(figsize=(25,25))
    plt.subplots_adjust(left=0.04, right=1.0, top=0.97, bottom=0.03)
    ax1 = fig.add_subplot(111)
    ax1.set_title('Stock Price Info')
    plt.xlabel('X = close/highest')
    plt.ylabel('Y = lowest/close')
    plt.scatter(x,y,s=5)
    font = {'family':'WenQuanYi Micro Hei','weight':'bold','size':8}
    matplotlib.rc("font",**font)
    parts = 20
    plt.xticks([w/parts for w in range(parts+1)], ['%.2f'%(w/parts) for w in range(parts+1)]) 
    plt.yticks([w/parts for w in range(parts+1)], ['%.2f'%(w/parts) for w in range(parts+1)]) 

    noted = []

    def on_button_press(event):
        print('event.button={}, type(event.buttont)={}'.format(event.button,type(event.button)))

        if event.button == 1:
            diffs = [(i, (x[i]-event.xdata)*(x[i]-event.xdata) + (y[i]-event.ydata)*(y[i]-event.ydata)) for i in range(len(x))]
            n = sorted(diffs, key=lambda x:x[1])[0][0]
            print('stock %s %s noted' % (df['code'].iloc[n], 'has been' if n in noted else 'will be'))
            if n not in noted:
                noted.append(n)
                code = codes[n]
                name = g_codes[code]
                code = code.split('.')[1]
                txt = '%s,%s' % (code, name)
                print('annoted txt %s' % txt)
                plt.annotate(txt, xy=(x[n],y[n]), xytext=(x[n]+0.003, y[n]+0.003))
                fig.canvas.draw_idle()
        elif event.button == 3:
            diffs = [(i, (x[i]-event.xdata)*(x[i]-event.xdata) + (y[i]-event.ydata)*(y[i]-event.ydata)) for i in range(len(x))]
            n = sorted(diffs, key=lambda x:x[1])[0][0]
            code = df.loc[n]['code']
            messagebox.showinfo(g_codes[code], 'code=%s\nprice=%.2f\nhighest=%.2f\nlowest=%.2f'%(code, df.iloc[n]['close'], df.iloc[n]['highest'], df.iloc[n]['lowest']))
            

    def on_key_press(event):
        axtemp=event.inaxes
        x_min,x_max=axtemp.get_xlim()
        y_min,y_max=axtemp.get_ylim()
        print('event.key=%s,x_min=%d,x_max=%d,y_min=%d,y_max=%d'%(event.key,x_min,x_max,y_min,y_max))
        x_fanwei = (x_max - x_min)/10
        y_fanwei = (x_max - y_min)/10
        if event.key=='pageup':
            axtemp.set(xlim=(x_min-x_fanwei, x_max+x_fanwei),ylim=(y_min-y_fanwei,y_max+y_fanwei))
        elif event.key == 'pagedown':
            axtemp.set(xlim=(x_min+x_fanwei, x_max-x_fanwei),ylim=(y_min+y_fanwei,y_max-y_fanwei))
        elif event.key == 'left':
            if x_fanwei > x_min: x_fanwei = x_min
            axtemp.set(xlim=(x_min-x_fanwei, x_max-x_fanwei))
        elif event.key == 'right':
            axtemp.set(xlim=(x_min+x_fanwei, x_max+x_fanwei))
        elif event.key=='up':
            if y_fanwei > y_min: y_fanwei = y_min
            axtemp.set(ylim=(y_min-y_fanwei,y_max-y_fanwei))
        elif event.key == 'down':
            axtemp.set(ylim=(y_min+y_fanwei,y_max+y_fanwei))
        elif event.key == 'enter':
            for n in range(len(x)):
                if n in noted: continue
                code = codes[n]
                name = g_codes[code]
                code = code.split('.')[1]
                txt = '%s,%s' % (code, name)
                plt.annotate(txt, xy=(x[n],y[n]), xytext=(x[n]+0.003, y[n]+0.003))
                noted.append(n)
        elif event.key == 'backspace':
           axtemp.set(xlim=(0,1),ylim=(0,1))
        else:
            return  
        fig.canvas.draw_idle()

    fig.canvas.mpl_disconnect(fig.canvas.manager.key_press_handler_id)#取消默认快捷键的注册
    fig.canvas.mpl_connect('key_press_event', on_key_press)
    fig.canvas.mpl_connect('button_press_event', on_button_press)
    
    #plt.ion()
    plt.show()

if __name__ == '__main__':
    df = get_stock_today()
    print('get today stock info success!')
        
    show_figure(df)   
