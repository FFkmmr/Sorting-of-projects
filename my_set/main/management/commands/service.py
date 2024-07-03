import csv
from django.core.management.base import BaseCommand
from main.models import Project, Technology, Industry

class import_csv(BaseCommand):
    help = 'Import projects from a CSV file'

    def handle(self):
        file_path = 'main/static/csv/data.csv'
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader: 
                technologies = row['technologies'].split(',')
                industries = row['industries'].split(',')

                project = Project.objects.create(
                    title=row['title'],
                    url=row['url'],
                    description=row['description'].strip(), 
                )

                for tech_name in technologies:
                    technology = Technology.objects.get_or_create(name=tech_name.strip())
                    project.technologies.add(technology)
    
                for industry_name in industries:
                    industry = Industry.objects.get_or_create(name=industry_name.strip())
                    project.industries.add(industry)

        self.stdout.write(self.style.SUCCESS('Successfully imported projects'))
