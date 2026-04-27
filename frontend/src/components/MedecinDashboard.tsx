import { useState } from 'react';

// Types
interface Dossier {
  dossier_id: string;
  malade_nom: string;
  malade_prenom: string;
  details: string;
  reclamations: Reclamation[];
}
interface Reclamation {
  reclamation_id: string;
  reclamation_status: string;
  reclamation_text: string;
}

interface MedecinDashboardProps {
  dossiers?: Dossier[];
}

export default function MedecinDashboard({ dossiers = [] }: MedecinDashboardProps) {
  const [editDossierId, setEditDossierId] = useState<string|null>(null);
  const [editForm, setEditForm] = useState<Partial<Dossier>>({});

  const handleEdit = (dossier: Dossier) => {
    setEditDossierId(dossier.dossier_id);
    setEditForm(dossier);
  };
  const handleSave = () => {
    // This part of the logic needs to be adapted if dossiers is not a state
    // For now, it will not update the dossiers prop directly.
    // If dossiers were a state, you would do:
    // setDossiers(dossiers.map(d => d.dossier_id === editDossierId ? { ...d, ...editForm } as Dossier : d));
    setEditDossierId(null);
    setEditForm({});
  };
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEditForm({ ...editForm, [e.target.name]: e.target.value });
  };

  return (
    <div className="max-w-4xl mx-auto py-10">
      <h2 className="text-2xl font-bold mb-6">Mes dossiers patients</h2>
      {dossiers.length === 0 ? (
        <p className="text-gray-500">Aucun dossier à afficher.</p>
      ) : dossiers.map(dossier => (
        <div key={dossier.dossier_id} className="mb-8 p-4 border rounded-lg bg-white dark:bg-gray-900">
          {editDossierId === dossier.dossier_id ? (
            <div className="space-y-2">
              <input name="malade_nom" value={editForm.malade_nom||''} onChange={handleChange} className="border p-2 rounded mr-2" placeholder="Nom malade" />
              <input name="malade_prenom" value={editForm.malade_prenom||''} onChange={handleChange} className="border p-2 rounded mr-2" placeholder="Prénom malade" />
              <input name="details" value={editForm.details||''} onChange={handleChange} className="border p-2 rounded mr-2" placeholder="Détails dossier" />
              <button onClick={handleSave} className="bg-blue-600 text-white px-4 py-2 rounded">Enregistrer</button>
            </div>
          ) : (
            <div>
              <div className="flex items-center gap-4 mb-2">
                <span className="font-semibold">{dossier.malade_prenom} {dossier.malade_nom}</span>
                <span className="text-sm text-gray-500">Dossier: {dossier.details}</span>
                <button onClick={() => handleEdit(dossier)} className="ml-2 text-blue-600 hover:underline">Modifier</button>
              </div>
              <div className="ml-4">
                <h4 className="font-semibold mb-1">Réclamations</h4>
                {dossier.reclamations.length === 0 ? <p className="text-gray-500">Aucune réclamation</p> : (
                  <ul className="list-disc ml-4">
                    {dossier.reclamations.map(rc => (
                      <li key={rc.reclamation_id}>
                        [{rc.reclamation_status}] {rc.reclamation_text}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
} 