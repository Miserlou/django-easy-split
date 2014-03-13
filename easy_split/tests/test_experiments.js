load("Widgets/Experiments/experiments.js");

var ExperimentsTestSuite = {
    setUp: function() {
        akoha.experiments.record_enrollment("test_experiment_control", "control");
        akoha.experiments.record_enrollment("test_experiment_test", "test");
    },
    testExperiments: function() {
        assertTrue(akoha.experiments.test("test_experiment_test"));
        assertFalse(akoha.experiments.control("test_experiment_test"));

        assertFalse(akoha.experiments.test("test_experiment_control"));
        assertTrue(akoha.experiments.control("test_experiment_control"));
    }
};
