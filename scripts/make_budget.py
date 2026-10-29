import pandas as pd, numpy as np, sys
src, out_wide, out_long = sys.argv[1:4]
df = pd.read_csv(src, encoding='latin1')
df['Order Date']=pd.to_datetime(df['Order Date'], dayfirst=True)

# quirk checks
pid = df.groupby('Product ID')['Product Name'].nunique()
print("Product IDs mapping to >1 Product Name:", (pid>1).sum(), "of", len(pid))
oid = df.groupby('Order ID')['Customer ID'].nunique()
print("Order IDs with >1 customer:", (oid>1).sum())
print("Ship before order:", (pd.to_datetime(df['Ship Date'], dayfirst=True) < df['Order Date']).sum())

# Budget for 2014 = 2013 actuals by Market x Category x Month, x1.08, with seeded noise
base = df[df['Order Date'].dt.year==2013].copy()
base['Month']=base['Order Date'].dt.month
g = base.groupby(['Market','Region','Category','Month'])[['Sales','Profit']].sum().reset_index()
rng = np.random.default_rng(2014)
g['Budget Sales']  = (g['Sales']  * 1.25 * rng.normal(1, 0.07, len(g))).round(0)
g['Budget Profit'] = (g['Profit'] * 1.28 * rng.normal(1, 0.09, len(g))).round(0)
g['Budget Year']=2014
long = g[['Budget Year','Market','Region','Category','Month','Budget Sales','Budget Profit']]
long.to_csv(out_long, index=False)

# wide: months as columns (what finance usually sends; user unpivots in Power Query)
months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
w = long.pivot_table(index=['Budget Year','Market','Region','Category'], columns='Month', values='Budget Sales', aggfunc='sum').fillna(0)
w.columns=[months[m-1] for m in w.columns]
w = w.reset_index()
w.to_csv(out_wide, index=False)
print("budget rows long:", len(long), "wide:", len(w))
print("2013 actual sales", round(base['Sales'].sum()), " 2014 budget", round(long['Budget Sales'].sum()), " 2014 actual", round(df[df['Order Date'].dt.year==2014]['Sales'].sum()))
# region x category variance preview for 2014
act = df[df['Order Date'].dt.year==2014].groupby(['Region','Category'])['Sales'].sum()
bud = long.groupby(['Region','Category'])['Budget Sales'].sum()
v = ((act-bud)/bud*100).round(1).unstack()
print(v)
