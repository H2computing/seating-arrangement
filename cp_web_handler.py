from flask import Flask, render_template, url_for, request, redirect
from SQLiteGenerator.SQLiteOOP import Class, Student, StudentRecords, Subject, SeatingArrangement
from database_handler import execute_sql
import random

app = Flask(__name__)

#display page
@app.route("/")
def display_all_student_records():
    classes = execute_sql("SELECT * FROM Class")
    students = execute_sql("SELECT * FROM Student")
    records = execute_sql("SELECT * FROM StudentRecords")
    subjects = execute_sql("SELECT * FROM Subject")

    for x in range(len(classes)-1): #to sort classes in order, so that when displayed will be according to class.
        smallest = x
        for y in range(x+1,len(classes)):
            if classes[y][0] < classes[smallest][0]:
                smallest = y
        if smallest != x:
            classes[smallest],classes[x] = classes[x],classes[smallest]

    for i in range(len(students)-1): #to sort reg.no in order, so that when displayed will be according to reg.no.
        smallest = i
        for j in range(i+1,len(students)):
            if students[j][1] < students[smallest][1]:
                smallest = j
        if smallest != i:
            students[smallest],students[i] = students[i],students[smallest]


    classes_oop = list(map(lambda a: Class(a[0],a[1]), classes))
    students_oop = list(map(lambda b: Student(b[0],b[1],b[2],b[3],b[4],b[5]), students ))
    records_oop = list(map(lambda c: StudentRecords(c[0],c[1],c[2]),records))
    subjects_oop = list(map(lambda d: Subject(d[0],d[1]), subjects ))

    # collating all grades and adding it as attribute to Students as AllSubjectGrades
    for student in students_oop:
        if student.get_AllSubjectGrades() == '':
            temp = ''
            index = 0
            while len(temp.split(' ')) - 1 != len(student.get_StudentSubjectCombi().split(' ')):
                for record in records:
                    if student.get_StudentName() == record[0] and student.get_StudentSubjectCombi().split(' ')[index] == record[2]:
                        temp += '{} '.format(record[1])
                index +=1
            temp = temp[:-1]
            student.set_AllSubjectGrades(temp)
            execute_sql(student.update_record())

    # Adding to WeakSubjects and StrongSubjects for seating arrangement
    # done in display so that after editing new strong subjects will be added and some removed as well
    # same for weak subjects
    for student in students_oop:
        student_seating_arrangement = execute_sql('SELECT * FROM SeatingArrangement WHERE StudentName = "{}"'.format(student.get_StudentName()))[0]
        StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo = student_seating_arrangement
        student_seating_arrangement = SeatingArrangement(StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo)
        StrongSubjects = ''
        WeakSubjects = ''
        for i in range(len(student.get_AllSubjectGrades().split(' '))):
            if student.get_AllSubjectGrades().split(' ')[i] < 'C': #'A', 'B'
                StrongSubjects += student.get_StudentSubjectCombi().split(' ')[i] + ' '
            elif student.get_AllSubjectGrades().split(' ')[i] > 'D':
                WeakSubjects += student.get_StudentSubjectCombi().split(' ')[i] + ' '
        student_seating_arrangement.set_StrongSubjects(StrongSubjects[:-1])
        student_seating_arrangement.set_WeakSubjects(WeakSubjects[:-1])
        execute_sql(student_seating_arrangement.update_record())

    reset_seating_arrangement()

    return render_template("display_all_records.html", classes = classes_oop, students = students_oop, records = records_oop, subjects = subjects_oop)

#edit records
@app.route("/edit_records/<string:student_name>", methods = ["GET","POST"])
def edit_student_record(student_name):
    student_details = execute_sql("SELECT * FROM Student WHERE StudentName = '{}'".format(student_name))[0]
    StudentName, StudentRegNo, ClassName, StudentSubjectCombi, StudentGender, AllSubjectGrades = student_details
    edit_student_details = Student(StudentName, StudentRegNo, ClassName, StudentSubjectCombi, StudentGender, AllSubjectGrades)

    #StudentName cannot be changed as its the Primary Key
    if request.method == 'POST':
        #Update Student Object
        edit_student_details.set_StudentRegNo(request.form.get('StudentRegNo').strip())
        edit_student_details.set_ClassName(request.form.get('ClassName').strip())
        edit_student_details.set_StudentGender(request.form.get('StudentGender').strip())

        new_StudentSubjectCombi = ''
        new_AllSubjectGrades = ''
        for i in range(len(StudentSubjectCombi.split(' '))):
            new_StudentSubjectCombi += request.form.get('SubjectName{}'.format(i).strip()) + ' '
            new_AllSubjectGrades += request.form.get('SubjectGrade{}'.format(i).strip()) + ' '
        new_StudentSubjectCombi = new_StudentSubjectCombi[:-1]
        new_AllSubjectGrades = new_AllSubjectGrades[:-1]

        edit_student_details.set_StudentSubjectCombi(new_StudentSubjectCombi)
        edit_student_details.set_AllSubjectGrades(new_AllSubjectGrades)

        # Update the database of Student
        execute_sql(edit_student_details.update_record())

        #Update StudentRecords object when change in grade
        index = 0
        if index < len(StudentSubjectCombi.split(' ')) and new_StudentSubjectCombi != StudentSubjectCombi:
            if new_StudentSubjectCombi.split(' ')[index] != StudentSubjectCombi.split(' ')[index]:
                student_subject = execute_sql("SELECT * FROM StudentRecords WHERE SubjectName = '{}'".format(StudentSubjectCombi.split(' ')[index]))[0]
                StudentName, SubjectGrade, SubjectName = student_subject
                edit_student_subject = StudentRecords(StudentName, SubjectGrade, SubjectName)
                edit_student_subject.set_SubjectName(new_StudentSubjectCombi.split(' ')[index])

                #Update the database of StudentRecords
                execute_sql(edit_student_subject.update_record())
            index += 1

        index = 0
        if index < len(AllSubjectGrades.split(' ')) and new_AllSubjectGrades != AllSubjectGrades:
            if new_AllSubjectGrades.split(' ')[index] != AllSubjectGrades.split(' ')[index]:
                student_grade = execute_sql("SELECT * FROM StudentRecords WHERE SubjectName = '{}'".format(StudentSubjectCombi.split(' ')[index]))[0]
                StudentName, SubjectGrade, SubjectName = student_grade
                edit_student_grade = StudentRecords(StudentName, SubjectGrade, SubjectName)
                edit_student_grade.set_SubjectName(new_AllSubjectGrades.split(' ')[index])
                #Update the database of StudentRecords
                execute_sql(edit_student_grade.update_record())
            index += 1

        #return to main page
        return redirect(url_for("display_all_student_records"))

    else:
        return render_template('edit_student_record.html', edit_student_details = edit_student_details, range = range(len(edit_student_details.get_AllSubjectGrades().split(' '))))

#delete student record
@app.route("/delete_student_record/<string:student_name>", methods = ['GET', 'POST'])
def delete_student_record(student_name):
    student_details = execute_sql("SELECT * FROM Student WHERE StudentName = '{}'".format(student_name))[0]
    StudentName, StudentRegNo, ClassName, StudentSubjectCombi, StudentGender, AllSubjectGrades = student_details
    delete_student_details = Student(StudentName, StudentRegNo, ClassName, StudentSubjectCombi, StudentGender, AllSubjectGrades)

    student_records = execute_sql("SELECT * FROM StudentRecords WHERE StudentName = '{}'".format(student_name))

    seating_arrangement_record = execute_sql("SELECT * FROM SeatingArrangement WHERE StudentName = '{}'".format(student_name))[0]
    StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo = seating_arrangement_record
    delete_seating_arrangement_record = SeatingArrangement(StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo)


    if request.method == 'POST':
        #Delete the database
        execute_sql(delete_student_details.delete_record())
        execute_sql(delete_seating_arrangement_record.delete_record())
        for i in range(len(student_records)):
            StudentName, SubjectGrade, SubjectName = student_records[i]
            delete_student_record = StudentRecords(StudentName, SubjectGrade, SubjectName)
            execute_sql(delete_student_record.delete_record())

        #Return to the main page
        return redirect(url_for("display_all_student_records"))

    else:
        return render_template('delete_student_record.html', delete_student_details = delete_student_details)

#Define subject names to their description:
def subject_description(subject_name):
    def subject(name):
        if name == 'CM':
            return 'Chemistry'
        elif name == 'BI':
            return "Biology"
        elif name == 'PH':
            return 'Physics'
        elif name == 'CP':
            return 'Computing'
        elif name == 'MA':
            return 'Mathematics'
        elif name == 'EC':
            return 'Economics'
        elif name == 'HI':
            return 'History'
        elif name == 'GE':
            return 'Geography'
        elif name == 'GP':
            return 'General Paper'
        elif name == 'CSC':
            return 'China Studies in Chinese'
        elif name == 'CSE':
            return 'China Studies in English'
        elif name == 'CLL':
            return 'Chinese Language and Literature'
        elif name == 'LIT':
            return ""
        elif name == 'FM':
            return "Further Mathematics"
        elif name == 'TS':
            return 'Translation'
        else:
            return ''

    if '(' in subject_name:
        if '1' in subject_name:
            h = 'H1'
        elif '3' in subject_name:
            h = 'H3'
        else:
            h = 'H2'

    name = subject(subject_name.strip().split('(')[:-1])

    if name == '':
        return ''
    else:
        return h + name

#Create Student Record
@app.route("/create_student_record", methods = ['GET','POST'])
def create_student_record():
    if request.method == 'POST':
        #Create Class object
        new_class = Class(request.form.get('ClassName'), '')
        execute_sql(new_class.create_new_record())

        #Create Student object
        new_student_details = Student(request.form.get('StudentName').strip(), request.form.get('StudentRegNo').strip(), request.form.get('ClassName').strip(),request.form.get('StudentSubjectCombi').strip(), request.form.get('StudentGender').strip(), request.form.get('AllSubjectGrades').strip())
        execute_sql(new_student_details.create_new_record())

        #Create StudentRecords object
        StudentSubjectCombi = request.form.get('StudentSubjectCombi').strip().split(' ')
        AllSubjectGrades = request.form.get('AllSubjectGrades').strip().split(' ')
        for i in range(len(StudentSubjectCombi)):
            new_student_record = StudentRecords(request.form.get('StudentName').strip(), AllSubjectGrades[i], StudentSubjectCombi[i])
            execute_sql(new_student_record.create_new_record())

        subject_lst = execute_sql('SELECT * FROM Subject')
        subject_lst = list(map(lambda tuple: tuple[0],subject_lst))
        for subject in StudentSubjectCombi:
            if subject not in subject_lst:
                new_subject = Subject(subject, subject_description(subject))
                execute_sql(new_subject.create_new_record())

        #Create Seating Arrangement object
        new_seating_arrangement = SeatingArrangement(request.form.get('StudentName'), CannotSeatNextTo = '', SeatInFront = False, WeakSubjects = '', StrongSubjects = '', ClassLst= '', SeatByGrades='', RowNo=0, ColumnNo=0)
        execute_sql(new_seating_arrangement.create_new_record())

        return redirect(url_for('display_all_student_records'))

    else:
        return render_template('create_student_record.html')

@app.route("/set_seating_arrangement")
def set_seating_arrangement():
    reset_seating_arrangement()
    return render_template('set_seating_arrangement.html')

@app.route("/class_seating_arrangement", methods = ['GET', 'POST'])
def class_seating_arrangement():
    valid_classes = execute_sql("SELECT * FROM Class")
    valid_classes = list(map(lambda x: x[0], valid_classes))

    if request.method == 'POST':
        ClassName = request.form.get('ClassName')
        return ClassName
    else:
        return render_template('class_seating_arrangement.html', valid_classes=valid_classes)

@app.route("/special_class_seating_arrangement", methods = ['GET', 'POST'])
def special_class_seating_arrangement():
    valid_classes = execute_sql("SELECT * FROM Class")
    valid_classes = list(map(lambda x: x[0], valid_classes))
    valid_subjects = execute_sql("SELECT * FROM Subject")
    valid_subjects = list(map(lambda x: x[0], valid_subjects))

    if request.method == 'POST':
        subject_taken = request.form.get('SubjectName')
        classes = ''
        for i in range(len(valid_classes)):
            ClassName = request.form.get('ClassName{}'.format(i))
            if ClassName != None:
                classes += ClassName + ' '
        classes = classes[:-1]
        return classes,subject_taken

    else:
        return render_template('special_class_seating_arrangement.html', valid_classes = valid_classes, class_range = range(len(valid_classes)), valid_subjects = valid_subjects)

@app.route("/set_student_details", methods=['GET', 'POST'])
def set_student_details():
    Subject = None
    lst = []

    if class_seating_arrangement() != None:
        ClassName = class_seating_arrangement()
        print(ClassName)
        lst = execute_sql("SELECT * FROM Student WHERE ClassName = '{}'".format(ClassName))
        lst = list(map(lambda x : x[0], lst)) #lst with all names of valid students
        print(lst)

    if special_class_seating_arrangement()[1] != None:
        ClassList, Subject = special_class_seating_arrangement()
        ClassList = ClassList.split(' ')
        lst = []
        for i in ClassList:
            temp = execute_sql("SELECT * FROM Student WHERE ClassName = '{}'".format(i))
            for student in temp:
                if Subject in student[3].split(' '):
                    lst.append(student)
        lst = list(map(lambda x : x[0], lst))

    if lst != []:
        string = ''
        for i in lst:
            string += i + ','
        string = string[:-1]

        for i in lst:
            #To identify, whether students belong to class which seating arrangement is generated for
            #set._ClassLst to lst for students in that class and set the rest of the students' ClassLst to default = []

            #set._ClassLst to lst for students in this class
            temp = execute_sql("SELECT * FROM SeatingArrangement WHERE StudentName = '{}'".format(i))[0]
            StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo = temp
            new_classlst = SeatingArrangement(StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo)
            new_classlst.set_ClassLst(string)
            execute_sql(new_classlst.update_record())

        #setting rest to default ClassLst = []
        student_lst = execute_sql("SELECT * FROM SeatingArrangement WHERE ClassLst != '{}'".format(string))
        print(student_lst)
        student_lst = list(map(lambda x: x[0], student_lst))
        for i in student_lst:
            temp = execute_sql("SELECT * FROM SeatingArrangement WHERE StudentName = '{}'".format(i))[0]
            StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst,  SeatByGrades, RowNo, ColumnNo = temp
            new_classlst = SeatingArrangement(StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects,StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo)
            new_classlst.set_ClassLst('')
            execute_sql(new_classlst.update_record())

        return render_template('set_student_details.html', Students=lst, student_range=range(len(lst)), range=range(5),Subject=Subject)

    if request.method == 'POST':
        seatbygrades = request.form.get('SeatByGrades')  # strong pupils will seat next to weak pupils
        rowno = request.form.get('RowNo')
        columnno = request.form.get('ColumnNo')
        print('set_student_details', seatbygrades, rowno, columnno)

        lst = execute_sql("SELECT * FROM SeatingArrangement WHERE ClassLst != ''")
        for student in lst:
            StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo = student
            student = SeatingArrangement(StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo)
            if seatbygrades == 'Yes':
                student.set_SeatByGrades(seatbygrades)
            if rowno != 0:
                student.set_RowNo(rowno)
                student.set_ColumnNo(columnno)
            execute_sql(student.update_record())

        lst = list(map(lambda x : x[0], lst)) #To get valid names

        for i in range(len(lst)):
            StudentName = lst[i]
            SeatInFront = request.form.get('SeatInFront{}'.format(i))
            if SeatInFront != None:
                student = execute_sql('SELECT * FROM SeatingArrangement WHERE StudentName = "{}"'.format(StudentName))[0]
                StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo = student
                set_student = SeatingArrangement(StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo)
                set_student.set_SeatInFront(True)
                execute_sql(set_student.update_record())

            StudentName1 = request.form.get('StudentName1{}'.format(i))
            StudentName2 = request.form.get('StudentName2{}'.format(i))

            if StudentName1 != '' and StudentName1 != None:
                print(StudentName1)
                print(execute_sql('SELECT * FROM SeatingArrangement WHERE StudentName = "{}"'.format(StudentName1)))
                student1 = execute_sql('SELECT * FROM SeatingArrangement WHERE StudentName = "{}"'.format(StudentName1))[0]
                StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo = student1
                set_student = SeatingArrangement(StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects,StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo)
                set_student.set_CannotSeatNextTo(StudentName2)
                execute_sql(set_student.update_record())

                student2 = execute_sql('SELECT * FROM SeatingArrangement WHERE StudentName = "{}"'.format(StudentName2))[0]
                StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo = student2
                set_student = SeatingArrangement(StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades,RowNo, ColumnNo)
                set_student.set_CannotSeatNextTo(StudentName1)
                execute_sql(set_student.update_record())


    else:
        return render_template('set_student_details.html', Students = lst, student_range = range(len(lst)), range = range(5), Subject = Subject)

def sort_by_grades(student_lst):
    #best scenario: Student A can help Student B and vice versa
    #strong and weak subjects of one must be opposite of the other student

    def mutual_benefit(weak, weak1, strong, strong1):
        #subject in weak must appear in strong1 and subject in strong must appear in weak1
        student1_benefit, student2_benefit = False, False

        for subject in weak:
            if subject in strong1:
                student1_benefit = True

        for subject in strong:
            if subject in weak1:
                student2_benefit = True

        if student1_benefit == True and student2_benefit == True:
            return True
        else:
            return False

    def only_one_benefit(weak, weak1, strong, strong1):
        student1_benefit, student2_benefit = False, False

        for subject in weak:
            if subject in strong1:
                student1_benefit = True

        for subject in strong:
            if subject in weak1:
                student2_benefit = True

        if student1_benefit == True or student2_benefit == True:
            return True
        else:
            return False

    grade_lst = []
    temp = []

    for i in range(len(student_lst)):
        Weak = student_lst[i][3].split(' ')
        Strong = student_lst[i][4].split(' ')

        for j in range(i+1, len(student_lst)):
            Weak1 = student_lst[j][3].split(' ')
            Strong1 = student_lst[j][4].split(' ')

            if mutual_benefit(Weak, Weak1, Strong, Strong1) == True:
                temp.append([student_lst[i],student_lst[j],'A']) #'A' will signify that it is the optimum pair
            elif only_one_benefit(Weak, Weak1, Strong, Strong1) == True and temp == [] :
                temp.append([student_lst[i], student_lst[j]])

        temp1 = list(filter(lambda x: 'A' in x, grade_lst))
        if temp1 == []: #if no optimum scenario for this student then it is okay to have pairs where only one can benefit
            grade_lst.extend(temp)
        else: #otherwise should only have optimum scenario for that student
            list(map(lambda x:x.remove(x[2]),temp1))
            grade_lst.extend(temp1)

        temp = []
    return grade_lst

@app.route("/generate_seating_arrangement", methods=['GET', 'POST'])
def generate_seating_arrangement():
    SeatInFront_lst = []
    not_SeatInFront_lst = [] #for students who do not need to seat in front, separate lst to randomly shuffle these students and then append it to SeatingArrangement_lst
    CannotSeatNextTo_lst = []
    SeatingArrangement_lst = []
    result = []

    student_lst = execute_sql("SELECT * FROM SeatingArrangement WHERE ClassLst != ''")
    StudentName_lst = list(map(lambda x:x[0], student_lst))
    ClassSize = len(StudentName_lst)

    StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo = student_lst[0]
    if RowNo == 0:
        set_student_details()

    student_lst = execute_sql("SELECT * FROM SeatingArrangement WHERE ClassLst != ''")
    StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo = student_lst[0]

    for student in student_lst:
        StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo = student
        student = SeatingArrangement(StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo)
        if student.get_CannotSeatNextTo() != '' and [student.get_StudentName(),student.get_CannotSeatNextTo()][::-1] not in SeatInFront_lst: #Assuming only one person cannot seat to that student
            CannotSeatNextTo_lst.append([student.get_StudentName(),student.get_CannotSeatNextTo()])
        if student.get_SeatInFront() == True:
            SeatInFront_lst.append(student.get_StudentName())


    if SeatByGrades == 'Yes':
        grade_lst = sort_by_grades(student_lst)
        #find pairs in cannotseatnextto_lst  that are also in grade_lst as those pairs can't seat next to each other
        for i in grade_lst:
            if i in CannotSeatNextTo_lst:
                grade_lst.remove(i)
            if i[::-1] in CannotSeatNextTo_lst:
                grade_lst.remove(i[::-1])

        #find pairs in grade_lst that are also in SeatInFrontLst to arrange the pairs in the front by appending confirmed pairs into SeatingArrangement_lst
        for a in range(len(SeatInFront_lst)):
            for b in range(a+1, len(SeatInFront_lst)):
                temp = [SeatInFront_lst[a], SeatInFront_lst[b]]
                if temp in grade_lst and temp[0] in StudentName_lst and temp[1] in StudentName_lst:
                    grade_lst.remove(temp)
                    SeatingArrangement_lst.append(temp) #added into confirmed seating arrangement
                    StudentName_lst.remove(temp[0])
                    StudentName_lst.remove(temp[1])

                if temp[::-1] in grade_lst and temp[0] in StudentName_lst and temp[1] in StudentName_lst:
                    grade_lst.remove(temp)
                    SeatingArrangement_lst.append(temp[::-1]) #added into confirmed seating arrangement
                    StudentName_lst.remove(temp[0])
                    StudentName_lst.remove(temp[1])

        # shuffle lst so that there will be more varieties of seating arrangement
        random.shuffle(CannotSeatNextTo_lst)
        random.shuffle(SeatInFront_lst)
        random.shuffle(grade_lst)

        # pair up those who are suppose to seat in front, seating in front prioritised to seating with those that can help with grades
        for s in range(len(SeatInFront_lst)):
            for r in range(s+1, len(SeatInFront_lst)):
                temp = [SeatInFront_lst[s], SeatInFront_lst[r]]
                if temp[0] in StudentName_lst and temp[1] in StudentName_lst:
                    SeatingArrangement_lst.append(temp)
                    StudentName_lst.remove(temp[0])
                    StudentName_lst.remove(temp[1])

        # all students supposed to seat in front are added
        random.shuffle(SeatingArrangement_lst)  # so that pairs in grade_lst won't always be in front

        # choose pairs from grade_lst
        for c in grade_lst:
            if c[0] in StudentName_lst and c[1] in StudentName_lst:
                not_SeatInFront_lst.append(c)
                StudentName_lst.remove(c[0])
                StudentName_lst.remove(c[1])


    else:
        # shuffle lst so that there will be more varieties of seating arrangement
        random.shuffle(CannotSeatNextTo_lst)
        random.shuffle(SeatInFront_lst)

        # pair up those who are suppose to seat in front
        for s in range(len(SeatInFront_lst)):
            for r in range(s + 1, len(SeatInFront_lst)):
                temp = [SeatInFront_lst[s], SeatInFront_lst[r]]
                if temp[0] in StudentName_lst and temp[1] in StudentName_lst:
                    SeatingArrangement_lst.append(temp)
                    StudentName_lst.remove(temp[0])
                    StudentName_lst.remove(temp[1])

    # pairing up any remaining students
    random.shuffle(StudentName_lst)
    while len(StudentName_lst) > 1:  # possible to have 1 student left if no pair for that student
        temp = [StudentName_lst[0], StudentName_lst[1]]
        if temp not in CannotSeatNextTo_lst and temp[::-1] not in CannotSeatNextTo_lst: #cannot be paired up if not suppose to seat next to each other
            not_SeatInFront_lst.append(temp)
            StudentName_lst.remove(temp[0])
            StudentName_lst.remove(temp[1])

    random.shuffle(not_SeatInFront_lst)
    SeatingArrangement_lst.extend(not_SeatInFront_lst)
    if StudentName_lst != []:
        SeatingArrangement_lst.append([StudentName_lst[0]])

    count = 0
    temp = []

    for row in range(RowNo):
        for column in range(ColumnNo):
            if count < ClassSize:
                temp.append(SeatingArrangement_lst[row*ColumnNo + column])
                if len(SeatingArrangement_lst[row*ColumnNo + column] ) == 2:
                    count += 2
                if len(SeatingArrangement_lst[row*ColumnNo + column]) == 1:
                    count += 1
        result.append(temp)
        temp = []

    return render_template('generate_seating_arrangement.html', SeatingArrangement_lst = result, RowNo = RowNo, ColumnNo = ColumnNo, RowNoRange = range(RowNo), ColumnNoRange = range(ColumnNo), ClassSize = ClassSize)

@app.route("/generate_seating_arrangement_again")
def generate_seating_arrangement_again():
    return generate_seating_arrangement()

def reset_seating_arrangement():
    #reset seating arrangement object when go back to display, and various setting menus (set_seating_arrangement, class_seating_arrangement, special_class_seating_arrangement)
    student_lst = execute_sql("SELECT * FROM SeatingArrangement WHERE ClassLst != ''")
    for student in student_lst:
        StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo = student
        student = SeatingArrangement(StudentName, CannotSeatNextTo, SeatInFront, WeakSubjects, StrongSubjects, ClassLst, SeatByGrades, RowNo, ColumnNo)
        student.set_CannotSeatNextTo('')
        student.set_SeatInFront(False)
        student.set_ClassLst('')
        student.set_SeatByGrades('')
        student.set_RowNo(0)
        student.set_ColumnNo(0)
        execute_sql(student.update_record())

# run app
if __name__ == "__main__":
    app.debug = True
    app.run()

 #hello
