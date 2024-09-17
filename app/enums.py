import enum

class Genre(enum.Enum):
    Alternative = 'Alternative'
    Blues = 'Blues'
    Classical = 'Classical'
    Country = 'Country'
    Electronic = 'Electronic'
    Folk = 'Folk'
    Funk = 'Funk'
    HipHop = 'Hip-Hop'
    Heavy_Metal = 'Heavy Metal'
    Instrumental = 'Instrumental'
    Jazz = 'Jazz'
    Musical_Theatre = 'Musical Theatre'
    Pop = 'Pop'
    Punk = 'Punk'
    RnB = 'R&B'
    Reggae = 'Reggae'
    Rock_n_Roll = 'Rock n Roll'
    Soul = 'Soul'
    Other = 'Other'

    @classmethod
    def choices(cls):
        """ Methods decorated with @classmethod can be called 
        statically without having an instance of the class."""
        return [(choice.name, choice.value) for choice in cls]

class State(enum.Enum):
    Abia_NG = "Abia, NG"
    Abuja_NG = "Abuja, NG"
    Adamawa_NG = "Adamawa, NG"
    Akwa_Ibom_NG = "Akwa Ibom, NG"
    Anambra_NG = "Anambra, NG"
    Bauchi_NG = "Bauchi, NG"
    Bayelsa_NG = "Bayelsa, NG"
    Benue_NG = "Benue, NG"
    Borno_NG = "Borno, NG"
    Cross_River_NG = "Cross River, NG"
    Delta_NG = "Delta, NG"
    Ebonyi_NG = "Ebonyi, NG"
    Edo_NG = "Edo, NG"
    Ekiti_NG = "Ekiti, NG"
    Enugu_NG = "Enugu, NG"
    Gombe_NG = "Gombe, NG"
    Imo_NG = "Imo, NG"
    Jigawa_NG = "Jigawa, NG"
    Kaduna_NG = "Kaduna, NG"
    Kano_NG = "Kano, NG"
    Katsina_NG = "Katsina, NG"
    Kebbi_NG = "Kebbi, NG"
    Kogi_NG = "Kogi, NG"
    Kwara_NG = "Kwara, NG"
    Lagos_NG = "Lagos, NG"
    Nasarawa_NG = "Nasarawa, NG"
    Niger_NG = "Niger, NG"
    Ogun_NG = "Ogun, NG"
    Ondo_NG = "Ondo, NG"
    Osun_NG = "Osun, NG"
    Oyo_NG = "Oyo, NG"
    Plateau_NG = "Plateau, NG"
    Rivers_NG = "Rivers, NG"
    Sokoto_NG = "Sokoto, NG"
    Taraba_NG = "Taraba, NG"
    Yobe_NG = "Yobe, NG"
    Zamfara_NG = "Zamfara, NG"

    @classmethod
    def choices(cls):
        return [(choice.name, choice.value) for choice in cls]
