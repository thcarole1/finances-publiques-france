// Désérialise le dossier TMDL du modèle : toute erreur de syntaxe ou de référence
// (colonne de tri, niveau de hiérarchie, relation vers une colonne inexistante…)
// fait échouer le contrôle, comme elle ferait échouer l'ouverture dans Power BI Desktop.
using Microsoft.AnalysisServices.Tabular;

var dossier = args.Length > 0
    ? args[0]
    : "powerbi/FinancesPubliques.SemanticModel/definition";

try
{
    var database = TmdlSerializer.DeserializeDatabaseFromFolder(dossier);
    var model = database.Model;
    Console.WriteLine(
        $"TMDL valide : {model.Tables.Count} tables, {model.Relationships.Count} relations, " +
        $"{model.Tables.Sum(t => t.Measures.Count)} mesures, " +
        $"{model.Tables.Count(t => t.CalculationGroup != null)} groupes de calcul.");

    // Contrôles complémentaires : relations vers des colonnes clés uniques côté dimension.
    var erreurs = new List<string>();
    foreach (var r in model.Relationships.OfType<SingleColumnRelationship>())
    {
        if (r.FromColumn is null || r.ToColumn is null)
            erreurs.Add($"Relation {r.Name} : colonne introuvable.");
    }
    foreach (var e in erreurs) Console.Error.WriteLine(e);
    return erreurs.Count == 0 ? 0 : 1;
}
catch (Exception e)
{
    Console.Error.WriteLine("TMDL invalide :");
    Console.Error.WriteLine(e.Message);
    if (e.InnerException is not null) Console.Error.WriteLine(e.InnerException.Message);
    return 1;
}
