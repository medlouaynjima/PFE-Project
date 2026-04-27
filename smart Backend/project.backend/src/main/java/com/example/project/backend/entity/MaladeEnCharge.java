package com.example.project.backend.entity;

import jakarta.persistence.*;

import java.io.Serializable;
import java.util.Objects;


@Entity

@Table(name = "MALADE_EN_CHARGE")
public class MaladeEnCharge implements Serializable {

    @Id
    @Column(name = "ID")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "NOM")
    private String nom;

    @Column(name = "PRENOM")
    private String prenom;

    @Column(name = "CIN")
    private String cin;

    @Column(name = "QUALITE")
    private String qualite;

    @ManyToOne
    @JoinColumn(name = "ID_ADHERENT")
    private Adherent adherent;


    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getNom() {
        return nom;
    }

    public void setNom(String nom) {
        this.nom = nom;
    }

    public String getPrenom() {
        return prenom;
    }

    public void setPrenom(String prenom) {
        this.prenom = prenom;
    }

    public String getCin() {
        return cin;
    }

    public void setCin(String cin) {
        this.cin = cin;
    }

    public String getQualite() {
        return qualite;
    }

    public void setQualite(String qualite) {
        this.qualite = qualite;
    }

    public Adherent getAdherent() {
        return adherent;
    }

    public void setAdherent(Adherent adherent) {
        this.adherent = adherent;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        MaladeEnCharge that = (MaladeEnCharge) o;
        return Objects.equals(id, that.id) && Objects.equals(nom, that.nom) && Objects.equals(prenom, that.prenom) && Objects.equals(cin, that.cin) && Objects.equals(qualite, that.qualite) && Objects.equals(adherent, that.adherent);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, nom, prenom, cin, qualite, adherent);
    }

    @Override
    public String toString() {
        return "MaladeEnCharge{" +
                "id=" + id +
                ", nom='" + nom + '\'' +
                ", prenom='" + prenom + '\'' +
                ", cin='" + cin + '\'' +
                ", qualite='" + qualite + '\'' +
                ", adherent=" + adherent +
                '}';
    }
}
