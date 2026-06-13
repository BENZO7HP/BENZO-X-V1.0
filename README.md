pkg update && pkg upgrade -y
pkg install python git -y
rm -rf BENZO-X
git clone --depth=1 https://github.com/BENZO7HP/BENZO-X
cd BENZO-X
pip install -r requirements.txt
python run.py



