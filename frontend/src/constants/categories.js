import { UserCheck, Code, Briefcase, Layers, Globe } from 'lucide-react'

export const INTERVIEW_CATEGORIES = [
  { 
    id: 'behavioral', 
    label: 'Behavioral', 
    icon: UserCheck, 
    desc: 'STAR method story-based scenario questions' 
  },
  { 
    id: 'technical', 
    label: 'Technical', 
    icon: Code, 
    desc: 'Coding, algorithms & system architecture' 
  },
  { 
    id: 'hr', 
    label: 'HR', 
    icon: Briefcase, 
    desc: 'Company fit, career goals & expectations' 
  },
  { 
    id: 'project', 
    label: 'Project', 
    icon: Layers, 
    desc: 'Past projects, leadership & metrics' 
  },
  { 
    id: 'general', 
    label: 'General', 
    icon: Globe, 
    desc: 'General interview practice questions' 
  }
]
