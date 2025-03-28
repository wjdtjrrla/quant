import pandas as pd
import numpy as np
from datetime import datetime

def create_ym(_df,
              _col='Adj Close'):
    df = _df.copy()
    
    # 인덱스 변경
    if 'Date' in df.index:
        df.set_index('Date')
    
    # 인덱스 시계열로 변경
    df.index = pd.to_datetime(df.index, utc=True)
    try:
        df.index = df.index.tz_localize(None)
    except Exception as e:
        print(e)
    
    # 데이터 중 결측, 양의 무한, 음의 무한 제외
    flag = df.isin([np.nan,np.inf,-np.inf]).any(axis=1)
    
    # 기준 컬럼 제외하고 삭제
    df = df.loc[~flag,[_col]]
    
    # 'STD-YM' 파생 생성 index에서 년 월 추출 대입
    df['STD-YM'] = df.index.strftime('%Y-%m')
    
    return df

def create_month(_df,
               _start = '2010-01-01',
               _end = datetime.now(),
               _momentum = 12,
               _select = 1):
    if _select ==1:
        # 월말 데이터 조건식
        flag = _df['STD-YM'] != _df.shift(-1)['STD-YM']
    elif _select == 0:
        # 월초 데이터 조건식
        flag = _df['STD-YM'] != _df.shift(1)['STD-YM']
    else:
        return print('_select의 값은 0 아니면 1 입니다.')
    result = _df.loc[flag]
    
    # 기준이 되는 컬럼의 이름을 변수에 저장
    col = result.columns[0]
    
    # 전월의 기준이 되는 컬럼의 값을 BF1에 대입
    result['BF1'] = result.shift(1)[col]
    # _momentum 값의 과거의 개월 수 데이터  BF2에 대입
    result['BF2'] = result.shift(_momentum)[col]
    try:
        result.index = result.index.dt.tz_localize(None)
    except Exception as e:
        print(e)        
    
    result = result.loc[_start : _end]
    
    
    return result
    
def create_trade(_df1,
                 _df2, 
                 _score=1):
    result = _df1.copy()
    result['trade'] = ''
        
    # 반복문 생성 -> df2를 기준으로 반복
    for idx in _df2.index:
        signal = ''
        
        momentum_index = _df2.loc[idx, 'BF1'] / _df2.loc[idx, 'BF2'] - _score
        
        flag = momentum_index > 0 and momentum_index != np.inf
        if flag:
            signal = 'buy'
        
        result.loc[idx:, 'trade'] = signal
    
    return result

def create_rtn(_df):
    result = _df.copy()
    result['rtn'] = 1

    col = result.columns[0]  # 첫 번째 열을 가격열로 간주
    prev_trade = result['trade'].shift(1)  # 이전 거래 상태 추출

    buy = None  # 매수 가격 저장용

    for idx in result.index:
        if prev_trade.loc[idx] == '' and result.loc[idx, 'trade'] == 'buy':
            buy = result.loc[idx, col]
            print(f'매수일 : {idx}, 매수가 : {buy}')

        elif prev_trade.loc[idx] == 'buy' and result.loc[idx, 'trade'] == '':
            sell = result.loc[idx, col]
            print(f'매도일 : {idx}, 매도가 : {sell}')

            rtn = sell / buy
            result.loc[idx, 'rtn'] = rtn
            print(f'수익률 : {rtn:.4f}')

    result['acc_rtn'] = result['rtn'].cumprod()
    acc_rtn = result['acc_rtn'].iloc[-1]

    return result, acc_rtn