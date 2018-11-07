$(function () {
    function saveEtud() {
        var nom = $("#nom").val();
        var prenom = $("#prenom").val();
        var note = $("#note").val();

        var success_alert = $("#success_alert");

        $.post("/api/etudiant", {nom: nom, prenom: prenom, note: note}, function (response) {
            console.log(response.id);
            $(success_alert).find("#success_message").text("Etudiant bien Ajouter avec ID:" + response.id);
            $(success_alert).removeClass("hidden");
            $("#nom").val('');
            $("#prenom").val('');
            $("#note").val('');
            //$(success_alert).alert();
        });
    }
    function saveInFile() {
        var success_alert = $("#success_alert");

        $.get("/api/save", function (response) {
            $(success_alert).find("#success_message").text("Fishier Bien Enregister");
            $(success_alert).removeClass("hidden");
            //$(success_alert).alert();
        });
    }// Handler for .ready() called.

    $.get("/api/tweet",function (data) {
        console.log(data)
    })
});

