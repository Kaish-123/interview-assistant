#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace std;

string ltrim(const string &str) {
    string s(str);
    s.erase(s.begin(), find_if(s.begin(), s.end(), [](unsigned char ch) {
        return !isspace(ch);
    }));
    return s;
}

string rtrim(const string &str) {
    string s(str);
    s.erase(find_if(s.rbegin(), s.rend(), [](unsigned char ch) {
        return !isspace(ch);
    }).base(), s.end());
    return s;
}

string trim(const string &str) {
    return rtrim(ltrim(str));
}

int check_log_history(vector<string> events) {
    static const int MAX_LOCK = 1000000;
    vector<int> lock_stack;
    vector<char> held(MAX_LOCK + 1, 0);

    const int n = static_cast<int>(events.size());

    for (int i = 0; i < n; ++i) {
        stringstream ss(events[i]);
        string op;
        int lock_id = 0;
        ss >> op >> lock_id;

        if (op == "ACQUIRE") {
            if (lock_id < 1 || lock_id > MAX_LOCK || held[lock_id]) {
                return i + 1;
            }
            held[lock_id] = 1;
            lock_stack.push_back(lock_id);
        } else {
            if (lock_id < 1 || lock_id > MAX_LOCK || !held[lock_id]) {
                return i + 1;
            }
            if (lock_stack.empty() || lock_stack.back() != lock_id) {
                return i + 1;
            }
            lock_stack.pop_back();
            held[lock_id] = 0;
        }
    }

    if (!lock_stack.empty()) {
        return n + 1;
    }
    return 0;
}

#ifdef LOCAL_TEST
int main() {
    auto run = [](vector<string> events, int expected) {
        int got = check_log_history(events);
        if (got != expected) {
            cerr << "FAIL expected " << expected << " got " << got << "\n";
            for (const auto &e : events) cerr << "  " << e << "\n";
            exit(1);
        }
    };

    run({"ACQUIRE 364", "ACQUIRE 84", "RELEASE 84", "RELEASE 364"}, 0);
    run({"ACQUIRE 364", "ACQUIRE 84", "RELEASE 364", "RELEASE 84"}, 3);
    run({"ACQUIRE 123", "ACQUIRE 364", "ACQUIRE 84", "RELEASE 84", "RELEASE 364", "ACQUIRE 456"}, 7);
    run({"ACQUIRE 123", "ACQUIRE 364", "ACQUIRE 84", "RELEASE 84", "RELEASE 364", "ACQUIRE 789", "RELEASE 456", "RELEASE 123"}, 7);
    run({"ACQUIRE 364", "ACQUIRE 84", "ACQUIRE 364"}, 3);
    run({}, 0);
    run({"ACQUIRE 1"}, 2);
    run({"ACQUIRE 1", "RELEASE 1"}, 0);
    run({"RELEASE 1"}, 1);
    run({"ACQUIRE 1", "ACQUIRE 1"}, 2);

    cout << "All tests passed\n";
    return 0;
}
#else
int main() {
    ofstream fout(getenv("OUTPUT_PATH"));

    string events_count_temp;
    getline(cin, events_count_temp);

    int events_count = stoi(ltrim(rtrim(events_count_temp)));

    vector<string> events(events_count);

    for (int i = 0; i < events_count; i++) {
        string events_item;
        getline(cin, events_item);

        events[i] = events_item;
    }

    int result = check_log_history(events);

    fout << result << "\n";
    fout.close();

    return 0;
}
#endif
