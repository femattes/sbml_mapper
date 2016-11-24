

import sqlite3

conn = sqlite3.connect('database.sqlite')
c = conn.cursor()

# Make new Table Parametrizations

# conn.execute('ALTER TABLE Parametrizations ADD COLUMN ID INT')
rowcount = c.execute('SELECT Count(*) FROM Parametrizations').fetchall()[0][0]
print(rowcount)

# for i in range(1, rowcount-1):
#   conn.execute('INSERT OR REPLACE INTO Parametrizations (ID) VALUES (' + str(i) + ')')


c.execute("SELECT * FROM Parametrizations")
colname_list = [tuple[0] for tuple in c.description]
new_colname_list = ['ID']
request_colnames = colname_list[0]
create_colnames = 'ID INTEGER PRIMARY KEY'
for name in colname_list:
    if (name[0] == 'K'):
        create_colnames = create_colnames + ', ' + name + ' INTEGER'
        new_colname_list.append(name)

    if (name[0] == 'K' and name != colname_list[0]):
        request_colnames = request_colnames + ', ' + name

#print(request_colnames)
#print(create_colnames)

if False:
    c.execute('CREATE TEMPORARY TABLE param_temp(' + request_colnames + ')')
    c.execute('INSERT INTO param_temp SELECT '+ request_colnames +' FROM Parametrizations')
    c.execute('DROP TABLE Parametrizations')
    c.execute('CREATE TABLE Parametrizations(' + create_colnames + ')')
    c.execute('INSERT INTO Parametrizations(' + request_colnames + ') SELECT ' + request_colnames + ' FROM param_temp')
    c.execute('DROP TABLE param_temp')
