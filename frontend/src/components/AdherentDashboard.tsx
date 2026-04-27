import { useState } from 'react';

// Types
interface Malade {
  malade_id: string;
  malade_nom: string;
  malade_prenom: string;
  cin: string;
  malade_qualite: string;
  dossiers: Dossier[];
}
interface Dossier {
  dossier_id: string;
  medecin_nom: string;
  medecin_prenom: string;
  remboursements: Remboursement[];
  reclamations: Reclamation[];
}
interface Remboursement {
  remboursement_id: string;
  total_rembourse: number;
  date_decision: string;
  type: string;
}
interface Reclamation {
  reclamation_id: string;
  reclamation_status: string;
  reclamation_text: string;
}

interface AdherentDashboardProps {
  malades?: Malade[];
}

export default function AdherentDashboard({ malades = [] }: AdherentDashboardProps) {
  const [editMaladeId, setEditMaladeId] = useState<string|null>(null);
  const [editForm, setEditForm] = useState<Partial<Malade>>({});

  const handleEdit = (malade: Malade) => {
    setEditMaladeId(malade.malade_id);
    setEditForm(malade);
  };
  const handleSave = () => {
    setMalades(malades.map(m => m.malade_id === editMaladeId ? { ...m, ...editForm } as Malade : m));
    setEditMaladeId(null);
    setEditForm({});
  };
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEditForm({ ...editForm, [e.target.name]: e.target.value });
  };

  return (
    <div className="max-w-4xl mx-auto py-10">
      <h2 className="text-2xl font-bold mb-6">Mes malades en charge</h2>
      {malades.length === 0 ? (
        <p className="text-gray-500">Aucun malade en charge à afficher.</p>
      ) : malades.map(malade => (
        <div key={malade.malade_id} className="mb-8 p-4 border rounded-lg bg-white dark:bg-gray-900">
          {editMaladeId === malade.malade_id ? (
            <div className="space-y-2">
              <input name="malade_nom" value={editForm.malade_nom||''} onChange={handleChange} className="border p-2 rounded mr-2" placeholder="Nom" />
              <input name="malade_prenom" value={editForm.malade_prenom||''} onChange={handleChange} className="border p-2 rounded mr-2" placeholder="Prénom" />
              <input name="cin" value={editForm.cin||''} onChange={handleChange} className="border p-2 rounded mr-2" placeholder="CIN" />
              <input name="malade_qualite" value={editForm.malade_qualite||''} onChange={handleChange} className="border p-2 rounded mr-2" placeholder="Qualité" />
              <button onClick={handleSave} className="bg-blue-600 text-white px-4 py-2 rounded">Enregistrer</button>
            </div>
          ) : (
            <div>
              <div className="flex items-center gap-4 mb-2">
                <span className="font-semibold">{malade.malade_prenom} {malade.malade_nom}</span>
                <span className="text-sm text-gray-500">CIN: {malade.cin} | Qualité: {malade.malade_qualite}</span>
                <button onClick={() => handleEdit(malade)} className="ml-2 text-blue-600 hover:underline">Modifier</button>
              </div>
              <div className="ml-4">
                <h4 className="font-semibold mb-1">Dossiers</h4>
                {malade.dossiers.length === 0 ? <p className="text-gray-500">Aucun dossier</p> : (
                  malade.dossiers.map(dossier => (
                    <div key={dossier.dossier_id} className="mb-2 p-2 border rounded bg-gray-50 dark:bg-gray-800">
                      <div className="font-medium">Dossier #{dossier.dossier_id} - Médecin: {dossier.medecin_prenom} {dossier.medecin_nom}</div>
                      <div className="ml-2">
                        <h5 className="font-semibold mt-2">Remboursements</h5>
                        {dossier.remboursements.length === 0 ? <p className="text-gray-500">Aucun remboursement</p> : (
                          <ul className="list-disc ml-4">
                            {dossier.remboursements.map(r => (
                              <li key={r.remboursement_id}>
                                {r.type} : {r.total_rembourse} € le {r.date_decision}
                              </li>
                            ))}
                          </ul>
                        )}
                        <h5 className="font-semibold mt-2">Réclamations</h5>
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
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
} 