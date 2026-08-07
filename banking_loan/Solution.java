import java.io.*;
import java.util.*;
import java.text.*;
import java.math.*;
import java.util.regex.*;
import java.util.stream.*;

interface Bank {
    void assignLoans(int[] loans);
    void averageLoan();
    void maxLoan();
    void minLoan();
}

abstract class LoanDept implements Bank {
    protected int[] loanAmounts;

    public LoanDept(int size) {
        loanAmounts = new int[size];
    }
}

class PersonalLoanDept extends LoanDept {
    public PersonalLoanDept(int clients) {
        super(clients);
    }

    @Override
    public void assignLoans(int[] loans) {
        int limit = Math.min(loanAmounts.length, loans.length);
        for (int i = 0; i < limit; i++) {
            loanAmounts[i] = loans[i];
        }
        System.out.println("Loans for clients processed");
    }

    @Override
    public void averageLoan() {
        if (loanAmounts.length == 0) {
            System.out.printf("Average loan amount for clients is %.2f%n", 0.0);
            return;
        }

        double sum = 0;
        for (int amount : loanAmounts) {
            sum += amount;
        }
        System.out.printf("Average loan amount for clients is %.2f%n", sum / loanAmounts.length);
    }

    @Override
    public void maxLoan() {
        if (loanAmounts.length == 0) {
            return;
        }

        int max = loanAmounts[0];
        for (int amount : loanAmounts) {
            if (amount > max) {
                max = amount;
            }
        }
        System.out.println("Maximum loan amount amongst clients is " + max);
    }

    @Override
    public void minLoan() {
        if (loanAmounts.length == 0) {
            return;
        }

        int min = loanAmounts[0];
        for (int amount : loanAmounts) {
            if (amount < min) {
                min = amount;
            }
        }
        System.out.println("Minimum loan amount amongst clients is " + min);
    }
}

class BusinessLoanDept extends LoanDept {
    public BusinessLoanDept(int businesses) {
        super(businesses);
    }

    @Override
    public void assignLoans(int[] loans) {
        int limit = Math.min(loanAmounts.length, loans.length);
        for (int i = 0; i < limit; i++) {
            loanAmounts[i] = loans[i];
        }
        System.out.println("Loans for businesses processed");
    }

    @Override
    public void averageLoan() {
        if (loanAmounts.length == 0) {
            System.out.printf("Average loan amount for businesses is %.2f%n", 0.0);
            return;
        }

        double sum = 0;
        for (int amount : loanAmounts) {
            sum += amount;
        }
        System.out.printf("Average loan amount for businesses is %.2f%n", sum / loanAmounts.length);
    }

    @Override
    public void maxLoan() {
        if (loanAmounts.length == 0) {
            return;
        }

        int max = loanAmounts[0];
        for (int amount : loanAmounts) {
            if (amount > max) {
                max = amount;
            }
        }
        System.out.println("Maximum loan amount amongst businesses is " + max);
    }

    @Override
    public void minLoan() {
        if (loanAmounts.length == 0) {
            return;
        }

        int min = loanAmounts[0];
        for (int amount : loanAmounts) {
            if (amount < min) {
                min = amount;
            }
        }
        System.out.println("Minimum loan amount amongst businesses is " + min);
    }
}

public class Solution {
    public static void main(String[] args) throws Exception {
        Scanner sc = new Scanner(System.in);

        String[] count = sc.nextLine().split(" ");
        int n = Integer.parseInt(count[0]);
        int m = Integer.parseInt(count[1]);

        PersonalLoanDept p = new PersonalLoanDept(n);
        BusinessLoanDept b = new BusinessLoanDept(m);

        count = sc.nextLine().split(" ");
        int[] loansClients = new int[n];
        for (int i = 0; i < n && i < count.length; i++) {
            loansClients[i] = Integer.parseInt(count[i]);
        }
        p.assignLoans(loansClients);

        count = sc.nextLine().split(" ");
        int[] loansBusinesses = new int[m];
        for (int i = 0; i < m && i < count.length; i++) {
            loansBusinesses[i] = Integer.parseInt(count[i]);
        }
        b.assignLoans(loansBusinesses);

        p.averageLoan();
        p.maxLoan();
        p.minLoan();

        b.averageLoan();
        b.maxLoan();
        b.minLoan();
    }
}
