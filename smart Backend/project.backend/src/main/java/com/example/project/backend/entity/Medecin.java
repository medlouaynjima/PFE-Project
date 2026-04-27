package com.example.project.backend.entity;

import com.example.project.backend.enums.UserRole;
import jakarta.persistence.*;

import java.io.Serializable;
import java.util.Date;
import java.util.Objects;

@Entity
@Table(name = "MEDECIN")
public class Medecin implements Serializable {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "ID")
    private Long id;

    @Column(name = "CIN")
    private String cin;

    @Column(name = "NOM")
    private String nom;

    @Column(name = "PRENOM")
    private String prenom;

    @Column(name = "GENRE")
    private String genre;

    @Column(name = "RIB")
    private String rib;

    @Column(name = "MAT_FISC")
    private String matriculeFiscale;

    @Column(name = "DATE_NAISSANCE")
    @Temporal(TemporalType.DATE)
    private Date dateDeNaissance;

    @Column(name = "GSM")
    private String gsm;

    @ManyToOne
    @JoinColumn(name = "ID_USER")
    private User user;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getCin() {
        return cin;
    }

    public void setCin(String cin) {
        this.cin = cin;
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

    public String getGenre() {
        return genre;
    }

    public void setGenre(String genre) {
        this.genre = genre;
    }

    public String getRib() {
        return rib;
    }

    public void setRib(String rib) {
        this.rib = rib;
    }

    public String getMatriculeFiscale() {
        return matriculeFiscale;
    }

    public void setMatriculeFiscale(String matriculeFiscale) {
        this.matriculeFiscale = matriculeFiscale;
    }

    public Date getDateDeNaissance() {
        return dateDeNaissance;
    }

    public void setDateDeNaissance(Date dateDeNaissance) {
        this.dateDeNaissance = dateDeNaissance;
    }

    public String getGsm() {
        return gsm;
    }

    public void setGsm(String gsm) {
        this.gsm = gsm;
    }

    public User getUser() {
        return user;
    }

    public void setUser(User user) {
        this.user = user;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Medecin medecin = (Medecin) o;
        return Objects.equals(id, medecin.id) && Objects.equals(cin, medecin.cin) && Objects.equals(nom, medecin.nom) && Objects.equals(prenom, medecin.prenom) && Objects.equals(genre, medecin.genre) && Objects.equals(rib, medecin.rib) && Objects.equals(matriculeFiscale, medecin.matriculeFiscale) && Objects.equals(dateDeNaissance, medecin.dateDeNaissance) && Objects.equals(gsm, medecin.gsm) && Objects.equals(user, medecin.user);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, cin, nom, prenom, genre, rib, matriculeFiscale, dateDeNaissance, gsm, user);
    }

    @Override
    public String toString() {
        return "Medecin{" +
                "id=" + id +
                ", cin='" + cin + '\'' +
                ", nom='" + nom + '\'' +
                ", prenom='" + prenom + '\'' +
                ", genre='" + genre + '\'' +
                ", rib='" + rib + '\'' +
                ", matriculeFiscale=" + matriculeFiscale +
                ", dateDeNaissance=" + dateDeNaissance +
                ", gsm='" + gsm + '\'' +
                ", user=" + user +
                '}';
    }
}
