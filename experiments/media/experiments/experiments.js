/**
 *   Used for split testing experiments.
 *   User participation to an experiment is available through:
 *       experiments.control("experiments_name");
 *   and
 *       experiments.test("experiments_name");
 *   Relies on JQuery
**/
experiments = function() {
    // experiment_enrollment should have the following format { experiment_name : group }
    var experiment_enrollment = {};

    return {
        record_enrollment: function(experiment_name, group) {
            experiment_enrollment[experiment_name] = group;
        },
        control: function(experiment_name) {
            if (experiment_enrollment[experiment_name]) {
                return experiment_enrollment[experiment_name] == "control";
            } else {
                if (console) {
                    console.error("Can't find experiment named " + experiment_name);
                }
                return true;
            }
        },
        test: function(experiment_name) {
            if (experiment_enrollment[experiment_name]) {
                return experiment_enrollment[experiment_name] == "test";
            } else {
                if (console) {
                    console.error("Can't find experiment named " + experiment_name);
                }
                return false;
            }
        },
        confirm_human: function() {
            $.get("/experiments/confirm_human/");
        }
    };
}();