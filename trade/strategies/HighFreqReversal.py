from trade.strategy import Strategy


class HighFreqReversal(Strategy):
    def __init__(self, profit1_keep_ratio=0.5, move_stop_to_breakeven=False,
                 candle_length=240,
                 kangaroo_min_pips=20, kangaroo_pin_divisor=3.0, kangaroo_room_left=10, kangaroo_room_divisor=5.0,
                 min_trend_score=-1, max_trend_score=1,
                 profit1_risk_ratio=1, profit2_risk_ratio=1,
                 pip_value=0.0001, signal_expiry=100, skip_minutes=240):

        self._candle_length = candle_length
        self._kangaroo_min_pips = kangaroo_min_pips
        self._kangaroo_pin_divisor = kangaroo_pin_divisor
        self._kangaroo_room_left = kangaroo_room_left
        self._kangaroo_room_divisor = kangaroo_room_divisor
        self._min_trend_score = min_trend_score
        self._max_trend_score = max_trend_score
        self._profit1_risk_ratio = profit1_risk_ratio
        self._profit2_risk_ratio = profit2_risk_ratio

        self._kangaroo_min_length = self._kangaroo_min_pips * pip_value

        super().__init__(profit1_keep_ratio, move_stop_to_breakeven, pip_value, signal_expiry, skip_minutes)


    def trade(self):
        df = self._data

        if not(self._is_trade_valid()):
            return
        
        prices = {
            'open_price': df['open_price'].tolist(),
            'high_price': df['high_price'].tolist(),
            'low_price': df['low_price'].tolist(),
            'close_price': df['close_price'].tolist()
        }
            
        candle = self._get_candle(prices, 0)
        trigger = self._get_trigger(candle)

        if self._is_kangaroo(prices, candle):
            trend_score = self._get_trend_score(prices, candle)

            if self._is_trend_score_valid(trigger['signal'], trend_score):
                self._new_order(trigger)
    

    def _get_candle(self, prices, index):
        return {
            'open_price': self._get_price(prices['open_price'], index, 'open'),
            'high_price': self._get_price(prices['high_price'], index, 'high'),
            'low_price': self._get_price(prices['low_price'], index, 'low'),
            'close_price': self._get_price(prices['close_price'], index, 'close')
        }
    

    def _get_trigger(self, candle):
        body_length = (candle['high_price'] - candle['low_price']) / self._kangaroo_pin_divisor

        # buy signal
        signal = 1
        entry = candle['high_price']
        stop = candle['low_price']
        risk = candle['high_price'] - candle['low_price']
        profit1 = candle['high_price'] + (self._profit1_risk_ratio * risk)
        profit2 = profit1 + (self._profit2_risk_ratio * risk)

        # sell signal
        if candle['open_price'] <= candle['low_price'] + body_length and candle['close_price'] <= candle['low_price'] + body_length:
            signal = -1
            entry = candle['low_price']
            stop = candle['high_price']
            risk = candle['high_price'] - candle['low_price']
            profit1 = candle['low_price'] - (self._profit1_risk_ratio * risk)
            profit2 = profit1 - (self._profit2_risk_ratio * risk)
        
        return {
            'signal': signal,
            'entry': entry,
            'stop': stop,
            'profit1': profit1,
            'profit2': profit2
        }
    
    
    def _get_trend_score(self, prices, candle):
        indexes = [8, 13, 21, 34, 55, 89, 144]
        uptrend = 0
        total = 0

        for i in indexes:
            try: 
                prev_price = self._get_price(prices['close_price'], i, 'close')
                total += 1
                if prev_price <= candle['close_price']:
                    uptrend += 1
            except:
                pass
        
        return (2 * uptrend / total) - 1
    
    
    def _is_trend_score_valid(self, signal, trend_score):
        min_trend_score = self._min_trend_score if signal == 1 else -self._max_trend_score
        max_trend_score = self._max_trend_score if signal == 1 else -self._min_trend_score

        return min_trend_score <= trend_score and trend_score <= max_trend_score


    
    def _is_kangaroo(self, prices, candle):
        open_price = candle['open_price']
        high_price = candle['high_price']
        low_price = candle['low_price']
        close_price = candle['close_price']

        if high_price- low_price < self._kangaroo_min_length:
            return False
        
        body_length = (high_price - low_price) / self._kangaroo_pin_divisor
        room_length = (high_price - low_price) / self._kangaroo_room_divisor

        # look for sell signals
        if open_price <= (low_price + body_length) and close_price <= (low_price + body_length):
            prev_high_price = self._get_price(prices['high_price'], 1, 'high')
            prev_low_price = self._get_price(prices['low_price'], 1, 'low')
            if open_price > prev_high_price or close_price > prev_high_price or open_price < prev_low_price or close_price < prev_low_price:
                return False
            for i in range(1, self._kangaroo_room_left + 1):
                if self._get_price(prices['high_price'], i, 'high') > (high_price - room_length):
                    return False
        # look for buy signals
        elif open_price >= (high_price - body_length) and close_price >= (high_price - body_length):
            prev_high_price = self._get_price(prices['high_price'], 1, 'high')
            prev_low_price = self._get_price(prices['low_price'], 1, 'low')
            if open_price > prev_high_price or close_price > prev_high_price or open_price < prev_low_price or close_price < prev_low_price:
                return False
            for i in range(1, self._kangaroo_room_left + 1):
                if self._get_price(prices['low_price'], i, 'low') < (low_price + room_length):
                    return False
        else:
            return False
        
        return True
    
    
    def _get_price(self, list, index, type):
        length = len(list)
        start_index = length - ((index + 1) * self._candle_length)
        end_index = length - (index * self._candle_length) - 1

        if end_index < 0:
            raise Exception("Candle out of bound.")
        
        start_index = max(0, start_index)

        if type == 'open':
            return list[start_index]
        elif type == 'close':
            return list[end_index]
        
        peak = list[start_index]
        for i in range(start_index + 1, end_index + 1):
            if (type == 'high' and peak < list[i]) or (type == 'low' and peak > list[i]):
                peak = list[i]
        
        return peak
