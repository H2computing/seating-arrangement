from SQLiteGenerator.SQLiteOOP import Class, Student, StudentRecords, Subject, SeatingArrangement
import sqlite3
import sys

debug = False

#Helper function, to execute 1 line of sql
def execute_sql(sql):
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    data = None #initialise data read from database

    if debug:
        print(sql)

    try:
        cursor.execute(sql)
        data = cursor.fetchall()
    except sqlite3.IntegrityError:
        print("Repeated Data")
    except:
        print("SQL Error: ", sys.exc_info()[0])

    conn.commit()

    cursor.close()
    conn.close()

    return data

#Create all SQL tables in the database
def create_table():
    execute_sql(Class.create_table())
    execute_sql(Student.create_table())
    execute_sql(StudentRecords.create_table())
    execute_sql(Subject.create_table())
    execute_sql(SeatingArrangement.create_table())

#create_table()

#read the file result_data.csv, process the data and create records in database
def read_file(file_name):
    with open(file_name) as f:
        line = f.readline()
        line = f.readline()
        while line:
            lst = line.split(';')
            ClassName = lst[0]
            TotalStudents = lst[1]
            StudentRegNo = lst[2]
            StudentName = lst[3]
            StudentGender = lst[4]
            StudentSubjectCombi = lst[5]
            SubjectName = lst[6]
            Description = lst[7]
            SubjectGrade = lst[8][:-1] #because of "\n" at the back
            c1 = Class(ClassName, TotalStudents)
            st1 = Student(StudentName, StudentRegNo, ClassName, StudentSubjectCombi, StudentGender, AllSubjectGrades = '')
            sr1 = StudentRecords(StudentName, SubjectGrade, SubjectName)
            sb1 = Subject(SubjectName, Description)
            sa1 = SeatingArrangement(StudentName, CannotSeatNextTo= '', SeatInFront= False,WeakSubjects='',StrongSubjects='', ClassLst = '', SeatByGrades= '' , RowNo = 0, ColumnNo=0)
            execute_sql(c1.create_new_record())
            execute_sql(st1.create_new_record())
            execute_sql(sr1.create_new_record())
            execute_sql(sb1.create_new_record())
            execute_sql(sa1.create_new_record())
            line = f.readline()
    #f.close()

#read_file('result_data.csv')