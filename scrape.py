import requests
from bs4 import BeautifulSoup
import csv

# Base URL of the course catalogue
base_url = 'https://apps.ualberta.ca/catalogue'

# Send a GET request to the main catalogue page
response = requests.get(base_url)
response.raise_for_status()  # Check for request errors

# Parse the main page content
soup = BeautifulSoup(response.text, 'html.parser')

# Find all faculty links
faculty_links = soup.select('ul.faculty-list a')

# Prepare a list to hold course data
courses = []

# Iterate over each faculty link
for faculty_link in faculty_links:
    faculty_url = base_url + faculty_link['href']
    faculty_response = requests.get(faculty_url)
    faculty_response.raise_for_status()
    faculty_soup = BeautifulSoup(faculty_response.text, 'html.parser')

    # Find all subject links within the faculty
    subject_links = faculty_soup.select('ul.subject-list a')

    # Iterate over each subject link
    for subject_link in subject_links:
        subject_url = base_url + subject_link['href']
        subject_response = requests.get(subject_url)
        subject_response.raise_for_status()
        subject_soup = BeautifulSoup(subject_response.text, 'html.parser')

        # Find all courses within the subject
        course_items = subject_soup.select('div.course-listing')

        # Extract course code and name
        for course_item in course_items:
            course_code = course_item.find('span', class_='course-code').text.strip()
            course_name = course_item.find('span', class_='course-title').text.strip()
            courses.append([course_code, course_name])

# Save the courses to a CSV file
with open('ualberta_courses.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Course Code', 'Course Name'])
    writer.writerows(courses)

print(f'Successfully scraped {len(courses)} courses.')
