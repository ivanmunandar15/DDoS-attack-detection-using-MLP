from datetime import datetime
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score

class MachineLearning():

    def __init__(self):
        
        print("Loading dataset ...")
        
        self.counter = 0
        
        self.flow_dataset = pd.read_csv('FlowStatsfile.csv')

        self.flow_dataset.iloc[:, 2] = self.flow_dataset.iloc[:, 2].str.replace('.', '')
        self.flow_dataset.iloc[:, 3] = self.flow_dataset.iloc[:, 3].str.replace('.', '')
        self.flow_dataset.iloc[:, 5] = self.flow_dataset.iloc[:, 5].str.replace('.', '')
        
        self.X_flow = self.flow_dataset.iloc[:, :-1].values
        self.X_flow = self.X_flow.astype('float64')

        self.y_flow = self.flow_dataset.iloc[:, -1].values

        self.X_flow_train, self.X_flow_test, self.y_flow_train, self.y_flow_test = train_test_split(self.X_flow, self.y_flow, test_size=0.25, random_state=0)

    def LR(self):
        
        print("------------------------------------------------------------------------------")
        print("Logistic Regression ...")

        self.classifier = LogisticRegression(solver='liblinear', random_state=0)
        self.Confusion_matrix()
        
    def Confusion_matrix(self):
        self.counter += 1
        
        self.flow_model = self.classifier.fit(self.X_flow_train, self.y_flow_train)

        self.y_flow_pred = self.flow_model.predict(self.X_flow_test)

        print("------------------------------------------------------------------------------")

        print("confusion matrix")
        cm = confusion_matrix(self.y_flow_test, self.y_flow_pred)
        print(cm)

        acc = accuracy_score(self.y_flow_test, self.y_flow_pred)

        print("succes accuracy = {0:.2f} %".format(acc*100))
        fail = 1.0 - acc
        print("fail accuracy = {0:.2f} %".format(fail*100))
        print("------------------------------------------------------------------------------")
        
        x = ['TP','FP','FN','TN']
        x_indexes = np.arange(len(x))
        width = 0.10
        plt.xticks(ticks=x_indexes, labels=x)
        plt.title("Résultats des algorithmes")
        plt.xlabel('Classe predite')
        plt.ylabel('Nombre de flux')
        plt.tight_layout()
        plt.style.use("seaborn-darkgrid")
        # plt.style.use("dark_background")
        # plt.style.use("ggplot")
        if self.counter == 1:
            y1 = [cm[0][0],cm[0][1],cm[1][0],cm[1][1]]
            plt.bar(x_indexes-2*width,y1, width=width, color="#1b7021", label='LR')
            plt.legend()
        
        
def main():
    
    start_script = datetime.now()
    
    ml = MachineLearning()
    
    start = datetime.now()
    ml.LR()
    end = datetime.now()
    print("LEARNING and PREDICTING Time: ", (end-start)) 
    
    end_script = datetime.now()
    print("Script Time: ", (end_script-start_script))

if __name__ == "__main__":
    main()