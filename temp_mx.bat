::FOR /L %%i IN (0,1,51) DO python MX.py --index %%i --threads 32 --clean 1

python MX.py --index 26 --threads 32 --clean 1
python MX.py --index 52 --threads 32 --clean 1