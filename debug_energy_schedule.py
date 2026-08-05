from ai.energy_management import smart_adaptive_schedule
consumption=[1.5]*24
generation=[3.0]*8+[0.5]*8+[2.0]*8
weather_forecast=[]
for i in range(24):
    if 8<=i<=15:
        weather_forecast.append({"hour":i,"temp_c":20,"precip_mm":0.0,"cloud_percent":85})
    else:
        weather_forecast.append({"hour":i,"temp_c":15,"precip_mm":0.0,"cloud_percent":20})
res=smart_adaptive_schedule(consumption,generation,10.0,soc=0.4,weather_forecast=weather_forecast,charge_threshold=0.3,discharge_threshold=0.7,max_charge_rate_kw=3.0)
print('morning actions:', [s['action'] for s in res['schedule'][0:8]])
print('afternoon actions:', [s['action'] for s in res['schedule'][8:16]])
print('morning charges:', sum(1 for s in res['schedule'][0:8] if 'charge' in s['action']))
print('afternoon charges:', sum(1 for s in res['schedule'][8:16] if 'charge' in s['action']))
print('soc timeline:', [s['soc'] for s in res['schedule']])
print('solar_confidence:', [s['solar_confidence'] for s in res['schedule']])
