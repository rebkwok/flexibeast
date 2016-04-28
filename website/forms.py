from django import forms


class ContactForm(forms.Form):

        first_name = forms.CharField(
            max_length=255, required=True,
            initial='',
            widget=forms.TextInput(
                attrs={'class': 'form-control'})
        )

        last_name = forms.CharField(
            max_length=255, required=True,
            initial='',
            widget=forms.TextInput(
                attrs={'class': 'form-control'})
        )

        email_address = forms.EmailField(
            max_length=255,
            required=True,
            widget=forms.TextInput(
                attrs={'class': 'form-control'})
        )

        subject = forms.ChoiceField(
            required=True,
            label="What can we help you with?",
            choices=(
                ('Workshop Enquiry', 'Workshop Enquiry'),
                ('Booking Enquiry', 'Booking Enquiry'),
                ('General Enquiry', 'General Enquiry')
            ),
            widget=forms.Select(attrs={'class': 'form-control input-xs disabled'})
        )
        other_subject = forms.CharField(
            max_length=255, required=False,
            label='Subject',
            initial='',
            widget=forms.TextInput(
                attrs={'class': 'form-control'})
        )

        cc = forms.BooleanField(
            widget=forms.CheckboxInput(attrs={
                    'class': "regular-checkbox",
                    'id': 'cc_id'
                }),
            label="Send me a copy of my email request",
            initial=True,
            required=False
        )

        message = forms.CharField(
            widget=forms.Textarea(attrs={'class': 'form-control email-message',
                                         'rows': 10}),
            label='Message',
            required=True)
